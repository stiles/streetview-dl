"""Core Street View downloading functionality."""

import base64
import io
import concurrent.futures as futures
import math
import re
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
from rich.console import Console

from .auth import get_api_key
from .metadata import StreetViewMetadata


class StreetViewDownloader:
    """Main class for downloading Street View panoramas."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
        backoff: float = 0.5,
    ):
        """Initialize downloader with API key and timeout."""
        self.api_key = api_key or get_api_key()
        self.timeout = timeout
        self._session_cache: Optional[str] = None
        self._http = self._build_session(retries=retries, backoff=backoff)

    @staticmethod
    def _build_session(retries: int, backoff: float) -> requests.Session:
        """Create a requests session with retry/backoff for transient errors."""
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            status=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _raise_for_api_error(self, response: requests.Response) -> None:
        """Report Google's error details without exposing the API key in URLs."""
        try:
            response.raise_for_status()
        except requests.HTTPError:
            error = {}
            try:
                payload = response.json()
                if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
                    error = payload["error"]
            except ValueError:
                pass

            parts = [f"Google Map Tiles API error (HTTP {response.status_code})"]
            endpoint = urlsplit(response.url or "").path
            if endpoint:
                parts.append(endpoint)
            if isinstance(error.get("status"), str):
                parts.append(error["status"])
            if isinstance(error.get("message"), str):
                parts.append(error["message"])
            for field in ("details", "errors"):
                details = error.get(field, [])
                if isinstance(details, list):
                    for detail in details:
                        if not isinstance(detail, dict):
                            continue
                        for name in ("reason", "message", "location"):
                            value = detail.get(name)
                            if isinstance(value, str) and value not in parts:
                                parts.append(value)
            if response.status_code == 403:
                parts.append(
                    "Check that Map Tiles API is enabled in the API key's project, "
                    "billing is active, and the key's API and application restrictions "
                    "allow requests from this CLI."
                )
            message = ": ".join(parts).replace(self.api_key, "[REDACTED]")
            raise requests.HTTPError(message, response=response) from None

    def create_session(self) -> str:
        """Create a session for the Map Tiles API."""
        if self._session_cache:
            return self._session_cache

        response = self._http.post(
            "https://tile.googleapis.com/v1/createSession",
            params={"key": self.api_key},
            json={
                "mapType": "streetview",
                "language": "en-US",
                "region": "US",
            },
            timeout=self.timeout,
        )
        self._raise_for_api_error(response)
        self._session_cache = response.json()["session"]
        return self._session_cache

    def get_metadata(
        self,
        pano_id: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius: int = 50,
    ) -> StreetViewMetadata:
        """Get metadata for a panorama by ID or coordinates."""
        session = self.create_session()
        params = {"session": session, "key": self.api_key}

        if pano_id:
            params["panoId"] = pano_id
        else:
            if lat is None or lng is None:
                raise ValueError(
                    "Must provide either pano_id or both lat and lng"
                )
            params.update({"lat": lat, "lng": lng, "radius": radius})

        response = self._http.get(
            "https://tile.googleapis.com/v1/streetview/metadata",
            params=params,
            timeout=self.timeout,
        )
        if (
            response.status_code in (400, 404)
            and pano_id
            and re.fullmatch(r"CI[A-Za-z0-9_-]{1,125}", pano_id)
        ):
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            error = payload.get("error") if isinstance(payload, dict) else None
            errors = error.get("errors") if isinstance(error, dict) else None
            expected_reason = {400: "invalidRequest", 404: "notFound"}[
                response.status_code
            ]
            if isinstance(errors, list) and any(
                isinstance(item, dict)
                and item.get("reason") == expected_reason
                for item in errors
            ):
                # Web photo IDs need the API's source-10 / field-2 envelope.
                # Wrap the same ID; never substitute a nearby panorama.
                raw_id = pano_id.encode("ascii")
                api_id = (
                    base64.urlsafe_b64encode(
                        b"\x08\x0a\x12" + bytes([len(raw_id)]) + raw_id
                    )
                    .decode("ascii")
                    .replace("=", ".")
                )
                response = self._http.get(
                    "https://tile.googleapis.com/v1/streetview/metadata",
                    params={**params, "panoId": api_id},
                    timeout=self.timeout,
                )
        self._raise_for_api_error(response)
        return StreetViewMetadata.from_api_response(response.json())

    def discover_historical_dates(
        self,
        lat: float,
        lng: float,
        radius: int = 50,
        max_depth: int = 7,
        max_panoramas: int = 200,
        console: Optional[Console] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover available historical dates for a location using enhanced traversal.
        
        This function aggressively searches for panoramas at different time periods
        by traversing linked panoramas with a breadth-first approach, prioritizing
        exploration of older dates to maximize historical discovery.
        
        Args:
            lat: Latitude of the location
            lng: Longitude of the location  
            radius: Initial search radius in meters (will try multiple radii)
            max_depth: Maximum link traversal depth (default: 7)
            max_panoramas: Maximum total panoramas to check (API call limit)
            console: Optional console for progress output
            
        Returns:
            List of dictionaries containing pano_id, date, and other metadata
            for each available historical panorama at this location.
            
        Note:
            This enhanced approach finds MORE historical dates than basic traversal,
            but still cannot access Google's complete internal timeline. The Map Tiles
            API does not expose the full historical timeline that the web interface shows.
        """
        
        if console:
            console.print(f"[cyan]Discovering historical imagery for location ({lat}, {lng})...[/cyan]")
            console.print(f"[dim]Search parameters: depth={max_depth}, max_panoramas={max_panoramas}[/dim]")
        
        # Track what we've found
        historical_by_date = {}  # date -> list of pano info
        checked_panos = set()
        
        # Queue: (pano_id, depth, date_priority)
        # date_priority: older dates get negative values for priority
        to_check = deque()
        
        # Start with multiple radius searches to cast a wide net
        initial_radii = [25, 50, 100, 150]
        if console:
            console.print(f"[dim]Searching at multiple radii: {initial_radii}[/dim]")
        
        for search_radius in initial_radii:
            try:
                metadata = self.get_metadata(lat=lat, lng=lng, radius=search_radius)
                if metadata.pano_id not in checked_panos:
                    checked_panos.add(metadata.pano_id)
                    
                    if metadata.date:
                        date_priority = self._date_to_priority(metadata.date)
                        to_check.append((metadata.pano_id, 0, date_priority))
                        
                        if metadata.date not in historical_by_date:
                            historical_by_date[metadata.date] = []
                        
                        historical_by_date[metadata.date].append({
                            'pano_id': metadata.pano_id,
                            'date': metadata.date,
                            'lat': metadata.lat,
                            'lng': metadata.lng,
                            'is_current': search_radius == initial_radii[0],
                        })
                        
                        if console and search_radius == initial_radii[0]:
                            console.print(f"  Found current panorama: {metadata.pano_id} ({metadata.date})")
            except Exception as e:
                if console and search_radius == initial_radii[0]:
                    console.print(f"[yellow]Warning: Could not get initial metadata: {e}[/yellow]")
        
        # Breadth-first search with priority for older dates
        while to_check and len(checked_panos) < max_panoramas:
            pano_id, depth, date_priority = to_check.popleft()
            
            if depth >= max_depth:
                continue
            
            try:
                metadata = self.get_metadata(pano_id=pano_id)
                
                # Record this date if we haven't seen it yet
                if metadata.date and metadata.date not in historical_by_date:
                    historical_by_date[metadata.date] = []
                    if console:
                        console.print(f"  [green]Found new date:[/green] {metadata.date} (pano: {metadata.pano_id}, depth: {depth})")
                
                if metadata.date:
                    # Add this panorama to the date's collection
                    pano_info = {
                        'pano_id': metadata.pano_id,
                        'date': metadata.date,
                        'lat': metadata.lat,
                        'lng': metadata.lng,
                        'is_current': False,
                        'depth': depth,
                    }
                    
                    # Only add if this specific pano_id isn't already in this date's list
                    if not any(p['pano_id'] == metadata.pano_id for p in historical_by_date[metadata.date]):
                        historical_by_date[metadata.date].append(pano_info)
                
                # Add linked panoramas to the queue
                if hasattr(metadata, 'links') and metadata.links:
                    for link in metadata.links:
                        linked_pano_id = link.get('panoId')
                        
                        if linked_pano_id and linked_pano_id not in checked_panos:
                            checked_panos.add(linked_pano_id)
                            
                            # Prioritize exploring older dates by using current date as priority
                            # Older dates get explored first
                            next_priority = date_priority
                            
                            to_check.append((linked_pano_id, depth + 1, next_priority))
                            
            except Exception as e:
                # Skip failed panoramas silently (common for invalid links)
                continue
        
        if console:
            console.print(f"[dim]Checked {len(checked_panos)} panoramas at {max_depth} levels deep[/dim]")
        
        # Convert to output format (one representative pano per date)
        historical_panoramas = []
        for date in sorted(historical_by_date.keys(), reverse=True):
            # Use the first panorama for this date
            pano_info = historical_by_date[date][0]
            pano_info['count'] = len(historical_by_date[date])  # How many panos have this date
            historical_panoramas.append(pano_info)
        
        if console:
            console.print(f"[green]Found {len(historical_panoramas)} unique date(s) from {len(checked_panos)} panoramas[/green]")
            
            # Show breakdown by decade for perspective
            decades = {}
            for date in historical_by_date.keys():
                if date:
                    decade = date[:3] + "0s"  # e.g., "2020-01" -> "2020s"
                    decades[decade] = decades.get(decade, 0) + 1
            
            if decades:
                console.print(f"[dim]Distribution: {', '.join(f'{k}: {v}' for k, v in sorted(decades.items()))}[/dim]")
        
        return historical_panoramas
    
    def _date_to_priority(self, date: Optional[str]) -> int:
        """
        Convert date string to priority value (older = lower number for priority queue).
        
        Args:
            date: Date string in format "YYYY-MM" or None
            
        Returns:
            Integer priority (lower = older = higher priority)
        """
        if not date:
            return 999999  # Unknown dates get lowest priority
        
        try:
            # Convert "YYYY-MM" to integer YYYYMM
            year_month = date.replace("-", "")
            return int(year_month)
        except:
            return 999999

    def fetch_tile(
        self, session: str, pano_id: str, z: int, x: int, y: int
    ) -> Image.Image:
        """Fetch a single tile image."""
        params = {"session": session, "key": self.api_key, "panoId": pano_id}
        url = f"https://tile.googleapis.com/v1/streetview/tiles/{z}/{x}/{y}"

        response = self._http.get(url, params=params, timeout=self.timeout)
        self._raise_for_api_error(response)
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    def download_panorama(
        self,
        metadata: StreetViewMetadata,
        quality: str = "medium",
        console: Optional[Console] = None,
        concurrency: int = 8,
    ) -> Image.Image:
        """Download and stitch panorama tiles."""
        # Small photo spheres have fewer zoom levels than Google's larger panoramas.
        native_zoom = max(
            0, min(5, math.ceil(math.log2(metadata.image_width / metadata.tile_width)))
        )
        zoom_offset = {"low": 2, "medium": 1, "high": 0}
        z = max(0, native_zoom - zoom_offset.get(quality, 0))

        session = self.create_session()

        # Calculate tile grid dimensions
        scale_factor = 2 ** (native_zoom - z)
        scaled_width = metadata.image_width // scale_factor
        scaled_height = metadata.image_height // scale_factor

        tiles_x = math.ceil(scaled_width / metadata.tile_width)
        tiles_y = math.ceil(scaled_height / metadata.tile_height)

        # Create canvas (suppress PIL warning for large images)
        canvas_width = tiles_x * metadata.tile_width
        canvas_height = tiles_y * metadata.tile_height

        # Temporarily disable PIL size warnings
        old_max = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None

        try:
            canvas = Image.new("RGB", (canvas_width, canvas_height))
        finally:
            Image.MAX_IMAGE_PIXELS = old_max

        total_tiles = tiles_x * tiles_y
        completed_tiles = 0

        if console:
            console.print(
                f"[dim]Downloading {total_tiles} tiles ({tiles_x}×{tiles_y})[/dim]"
            )

        # Prepare coordinates
        coords = [(x, y) for y in range(tiles_y) for x in range(tiles_x)]

        # Define worker that only fetches and returns
        def fetch_coord(coord: tuple[int, int]):
            x, y = coord
            tile = self.fetch_tile(session, metadata.pano_id, z, x, y)
            return x, y, tile

        # Download tiles in parallel; paste on main thread to avoid PIL concurrency issues
        with futures.ThreadPoolExecutor(
            max_workers=max(1, concurrency)
        ) as executor:
            future_map = {executor.submit(fetch_coord, c): c for c in coords}
            for fut in futures.as_completed(future_map):
                x, y, tile = fut.result()
                canvas.paste(
                    tile,
                    (x * metadata.tile_width, y * metadata.tile_height),
                )
                completed_tiles += 1

        if console:
            console.print(
                f"[dim]Downloaded {completed_tiles} tiles successfully[/dim]"
            )

        # Crop to exact panorama dimensions
        # Temporarily disable PIL size warnings for cropping
        old_max = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None

        try:
            result = canvas.crop((0, 0, scaled_width, scaled_height))
        finally:
            Image.MAX_IMAGE_PIXELS = old_max

        return result

    def download_from_url(
        self,
        url: str,
        quality: str = "medium",
        console: Optional[Console] = None,
    ) -> Tuple[Image.Image, StreetViewMetadata]:
        """Download panorama from Google Maps URL."""
        from .metadata import extract_from_maps_url

        pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(url)
        if not pano_id:
            raise ValueError("Could not extract panorama ID from URL")

        metadata = self.get_metadata(pano_id=pano_id)
        metadata.url_yaw = yaw
        metadata.url_pitch = pitch
        metadata.url_fov = fov
        metadata.url_mode_token = mode_token
        metadata.url_date = url_date

        image = self.download_panorama(metadata, quality, console)
        return image, metadata

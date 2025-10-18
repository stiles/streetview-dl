"""Core Street View downloading functionality."""

import io
import concurrent.futures as futures
import math
from typing import Optional, Tuple

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
        response.raise_for_status()
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
        response.raise_for_status()
        return StreetViewMetadata.from_api_response(response.json())

    def fetch_tile(
        self, session: str, pano_id: str, z: int, x: int, y: int
    ) -> Image.Image:
        """Fetch a single tile image."""
        params = {"session": session, "key": self.api_key, "panoId": pano_id}
        url = f"https://tile.googleapis.com/v1/streetview/tiles/{z}/{x}/{y}"

        response = self._http.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    def download_panorama(
        self,
        metadata: StreetViewMetadata,
        quality: str = "medium",
        console: Optional[Console] = None,
        concurrency: int = 8,
    ) -> Image.Image:
        """Download and stitch panorama tiles."""
        # Map quality to zoom level
        zoom_map = {"low": 3, "medium": 4, "high": 5}
        z = zoom_map.get(quality, 5)

        session = self.create_session()

        # Calculate tile grid dimensions
        scale_factor = 2 ** (5 - z)  # Scale down from max resolution
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
            try:
                tile = self.fetch_tile(session, metadata.pano_id, z, x, y)
                return x, y, tile
            except requests.exceptions.RequestException:
                return x, y, None

        # Download tiles in parallel; paste on main thread to avoid PIL concurrency issues
        with futures.ThreadPoolExecutor(
            max_workers=max(1, concurrency)
        ) as executor:
            future_map = {executor.submit(fetch_coord, c): c for c in coords}
            for fut in futures.as_completed(future_map):
                x, y, tile = fut.result()
                if tile is not None:
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

        pano_id, yaw, pitch, fov, mode_token = extract_from_maps_url(url)
        if not pano_id:
            raise ValueError("Could not extract panorama ID from URL")

        metadata = self.get_metadata(pano_id=pano_id)
        metadata.url_yaw = yaw
        metadata.url_pitch = pitch
        metadata.url_fov = fov
        metadata.url_mode_token = mode_token

        image = self.download_panorama(metadata, quality, console)
        return image, metadata

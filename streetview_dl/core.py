"""Core Street View downloading functionality."""

import io
import math
from typing import Optional, Tuple

import requests
from PIL import Image
from rich.progress import Progress, TaskID

from .auth import get_api_key
from .metadata import StreetViewMetadata


class StreetViewDownloader:
    """Main class for downloading Street View panoramas."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize downloader with API key and timeout."""
        self.api_key = api_key or get_api_key()
        self.timeout = timeout
        self._session_cache: Optional[str] = None
    
    def create_session(self) -> str:
        """Create a session for the Map Tiles API."""
        if self._session_cache:
            return self._session_cache
            
        response = requests.post(
            "https://tile.googleapis.com/v1/createSession",
            params={"key": self.api_key},
            json={"mapType": "streetview", "language": "en-US", "region": "US"},
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
        radius: int = 50
    ) -> StreetViewMetadata:
        """Get metadata for a panorama by ID or coordinates."""
        session = self.create_session()
        params = {"session": session, "key": self.api_key}
        
        if pano_id:
            params["panoId"] = pano_id
        else:
            if lat is None or lng is None:
                raise ValueError("Must provide either pano_id or both lat and lng")
            params.update({"lat": lat, "lng": lng, "radius": radius})
        
        response = requests.get(
            "https://tile.googleapis.com/v1/streetview/metadata", 
            params=params, 
            timeout=self.timeout
        )
        response.raise_for_status()
        return StreetViewMetadata.from_api_response(response.json())
    
    def fetch_tile(self, session: str, pano_id: str, z: int, x: int, y: int) -> Image.Image:
        """Fetch a single tile image."""
        params = {"session": session, "key": self.api_key, "panoId": pano_id}
        url = f"https://tile.googleapis.com/v1/streetview/tiles/{z}/{x}/{y}"
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    
    def download_panorama(
        self, 
        metadata: StreetViewMetadata, 
        quality: str = "high",
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
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
        
        # Create canvas
        canvas_width = tiles_x * metadata.tile_width
        canvas_height = tiles_y * metadata.tile_height
        canvas = Image.new("RGB", (canvas_width, canvas_height))
        
        total_tiles = tiles_x * tiles_y
        completed_tiles = 0
        
        # Download and place tiles
        for y in range(tiles_y):
            for x in range(tiles_x):
                try:
                    tile = self.fetch_tile(session, metadata.pano_id, z, x, y)
                    canvas.paste(tile, (x * metadata.tile_width, y * metadata.tile_height))
                except requests.exceptions.RequestException:
                    # Skip missing tiles (some panoramas have gaps)
                    pass
                
                completed_tiles += 1
                if progress and task_id:
                    progress.update(task_id, completed=completed_tiles)
        
        # Crop to exact panorama dimensions
        return canvas.crop((0, 0, scaled_width, scaled_height))
    
    def download_from_url(
        self, 
        url: str, 
        quality: str = "high",
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> Tuple[Image.Image, StreetViewMetadata]:
        """Download panorama from Google Maps URL."""
        from .metadata import extract_from_maps_url
        
        pano_id, yaw, pitch = extract_from_maps_url(url)
        if not pano_id:
            raise ValueError("Could not extract panorama ID from URL")
        
        metadata = self.get_metadata(pano_id=pano_id)
        metadata.url_yaw = yaw
        metadata.url_pitch = pitch
        
        image = self.download_panorama(metadata, quality, progress, task_id)
        return image, metadata

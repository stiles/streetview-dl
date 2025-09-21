"""Street View metadata extraction and handling."""

import re
import urllib.parse as urlparse
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field


class StreetViewMetadata(BaseModel):
    """Street View panorama metadata."""
    
    pano_id: str = Field(..., description="Panorama ID")
    image_width: int = Field(..., description="Full panorama width in pixels")
    image_height: int = Field(..., description="Full panorama height in pixels") 
    tile_width: int = Field(..., description="Individual tile width")
    tile_height: int = Field(..., description="Individual tile height")
    
    # Location data
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    
    # Capture info
    date: Optional[str] = Field(None, description="Capture date")
    copyright_info: Optional[str] = Field(None, description="Copyright information")
    
    # URL-extracted info
    url_yaw: Optional[float] = Field(None, description="Yaw from URL")
    url_pitch: Optional[float] = Field(None, description="Pitch from URL")
    
    # Additional metadata
    links: Optional[Any] = Field(None, description="Links to nearby panoramas")
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "StreetViewMetadata":
        """Create metadata from API response."""
        return cls(
            pano_id=data["panoId"],
            image_width=data["imageWidth"],
            image_height=data["imageHeight"],
            tile_width=data["tileWidth"],
            tile_height=data["tileHeight"],
            lat=data.get("lat"),
            lng=data.get("lng"),
            date=data.get("date"),
            copyright_info=data.get("copyright"),
            links=data.get("links"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return self.model_dump(exclude_none=True)


def extract_from_maps_url(url: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Extract panorama ID, yaw, and pitch from Google Maps URL.
    
    Returns:
        Tuple of (pano_id, yaw, pitch). Values may be None if not found.
    """
    # Parse URL to get path and query components
    parsed = urlparse.urlparse(url)
    haystack = (parsed.path or "") + "?" + (parsed.query or "")
    
    # Try to extract from embedded thumbnail URL in the data parameter
    thumbnail_match = re.search(r"https:%2F%2Fstreetviewpixels.*?%3F([^!]+)", haystack)
    if thumbnail_match:
        # Decode the query string from the thumbnail URL
        qs_encoded = thumbnail_match.group(1)
        qs_decoded = qs_encoded.replace("%26", "&").replace("%3D", "=")
        qs_params = urlparse.parse_qs(qs_decoded)
        
        pano_id = qs_params.get("panoid", [None])[0]
        yaw_str = qs_params.get("yaw", ["0"])[0]
        pitch_str = qs_params.get("pitch", ["0"])[0]
        
        try:
            yaw = float(yaw_str) if yaw_str else None
            pitch = float(pitch_str) if pitch_str else None
        except (ValueError, TypeError):
            yaw = pitch = None
            
        return pano_id, yaw, pitch
    
    # Fallback: try to extract panorama ID from the !1s token pattern
    pano_match = re.search(r"!3m5!1s([^!]+)", haystack)
    if pano_match:
        return pano_match.group(1), None, None
    
    # Last resort: try direct panoid parameter
    pano_match = re.search(r"[?&]panoid=([^&]+)", haystack)
    if pano_match:
        return pano_match.group(1), None, None
    
    return None, None, None


def validate_maps_url(url: str) -> bool:
    """Check if URL looks like a valid Google Maps Street View URL."""
    if not url:
        return False
    
    # Must be a Google Maps domain
    if not any(domain in url.lower() for domain in ["maps.google.com", "google.com/maps"]):
        return False
    
    # Must contain Street View indicators
    street_view_indicators = [
        "3a,",           # classic Street View path token
        "streetview",    # explicit keyword
        "!1e1",          # SV layer marker in data blob
        "data=!3m",      # generic data blob marker
        "map_action=pano",  # API=1 pano deep link
        "panoid=",       # direct pano id parameter
    ]
    return any(indicator in url for indicator in street_view_indicators)

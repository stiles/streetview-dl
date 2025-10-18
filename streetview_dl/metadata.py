"""Street View metadata extraction and handling."""

import re
import urllib.parse as urlparse
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field


class StreetViewMetadata(BaseModel):
    """Street View panorama metadata."""

    pano_id: str = Field(..., description="Panorama ID")
    image_width: int = Field(..., description="Full panorama width in pixels")
    image_height: int = Field(
        ..., description="Full panorama height in pixels"
    )
    tile_width: int = Field(..., description="Individual tile width")
    tile_height: int = Field(..., description="Individual tile height")

    # Location data
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    original_lat: Optional[float] = Field(None, description="Original latitude")
    original_lng: Optional[float] = Field(None, description="Original longitude")
    original_elevation_above_egm96: Optional[float] = Field(
        None, description="Original elevation above EGM96 in meters"
    )

    # Camera orientation from API
    heading: Optional[float] = Field(None, description="Compass heading in degrees")
    tilt: Optional[float] = Field(None, description="Camera tilt/pitch in degrees")
    roll: Optional[float] = Field(None, description="Camera roll rotation in degrees")

    # Capture info
    date: Optional[str] = Field(None, description="Capture date")
    copyright_info: Optional[str] = Field(
        None, description="Copyright information"
    )
    imagery_type: Optional[str] = Field(
        None, description="Imagery type: indoor or outdoor"
    )

    # URL-extracted info
    url_yaw: Optional[float] = Field(None, description="Yaw from URL")
    url_pitch: Optional[float] = Field(None, description="Pitch from URL")
    url_fov: Optional[float] = Field(None, description="Field of view from URL")
    url_mode_token: Optional[str] = Field(
        None, description="Street View mode token from URL (e.g., '3a')"
    )

    # Address and problem reporting
    address_components: Optional[Any] = Field(
        None, description="Structured address components"
    )
    report_problem_link: Optional[str] = Field(
        None, description="Link for reporting problems with this panorama"
    )

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
            original_lat=data.get("originalLat"),
            original_lng=data.get("originalLng"),
            original_elevation_above_egm96=data.get("originalElevationAboveEgm96"),
            heading=data.get("heading"),
            tilt=data.get("tilt"),
            roll=data.get("roll"),
            date=data.get("date"),
            copyright_info=data.get("copyright"),
            imagery_type=data.get("imageryType"),
            address_components=data.get("addressComponents"),
            report_problem_link=data.get("reportProblemLink"),
            links=data.get("links"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return self.model_dump(exclude_none=True)


def extract_from_maps_url(
    url: str,
) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[float], Optional[str]]:
    """
    Extract panorama ID, yaw, pitch, FOV, and mode token from Google Maps URL.

    Returns:
        Tuple of (pano_id, yaw, pitch, fov, mode_token). Values may be None if not found.
    """
    # Parse URL to get path and query components
    parsed = urlparse.urlparse(url)
    haystack = (parsed.path or "") + "?" + (parsed.query or "")
    
    # Extract Street View mode token and FOV from URL path
    mode_token = None
    fov = None
    
    # Look for Street View mode token (e.g., "3a")
    mode_match = re.search(r",(\d+a),", haystack)
    if mode_match:
        mode_token = mode_match.group(1)
    
    # Look for field of view (e.g., "75y")
    fov_match = re.search(r",(\d+(?:\.\d+)?)y,", haystack)
    if fov_match:
        try:
            fov = float(fov_match.group(1))
        except (ValueError, TypeError):
            fov = None

    # Try to extract from embedded thumbnail URL in the data parameter
    thumbnail_match = re.search(
        r"https:%2F%2Fstreetviewpixels.*?%3F([^!]+)", haystack
    )
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

        return pano_id, yaw, pitch, fov, mode_token

    # Fallback: try to extract panorama ID from the !1s token pattern
    pano_match = re.search(r"!3m5!1s([^!]+)", haystack)
    if pano_match:
        return pano_match.group(1), None, None, fov, mode_token

    # Last resort: try direct panoid parameter
    pano_match = re.search(r"[?&]panoid=([^&]+)", haystack)
    if pano_match:
        return pano_match.group(1), None, None, fov, mode_token

    return None, None, None, fov, mode_token


def validate_maps_url(url: str) -> bool:
    """Check if URL looks like a valid Google Maps Street View URL."""
    if not url:
        return False

    # Must be a Google Maps domain
    if not any(
        domain in url.lower()
        for domain in ["maps.google.com", "google.com/maps"]
    ):
        return False

    # Must contain Street View indicators
    street_view_indicators = [
        "3a,",  # classic Street View path token
        "streetview",  # explicit keyword
        "!1e1",  # SV layer marker in data blob
        "data=!3m",  # generic data blob marker
        "map_action=pano",  # API=1 pano deep link
        "panoid=",  # direct pano id parameter
    ]
    return any(indicator in url for indicator in street_view_indicators)

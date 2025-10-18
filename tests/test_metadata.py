import pytest

from streetview_dl.metadata import (
    extract_from_maps_url,
    validate_maps_url,
    StreetViewMetadata,
)


def test_validate_maps_url_true():
    # contains Street View markers
    url = "https://www.google.com/maps/@?api=1&map_action=pano&parameters"
    assert validate_maps_url(url) is True


def test_validate_maps_url_false():
    assert validate_maps_url("https://example.com/") is False


def test_extract_from_maps_url_thumbnail_query():
    # Minimal synthetic URL including an encoded thumbnail query with panoid, yaw, pitch
    qs = "panoid%3DTESTPANO%26yaw%3D123.45%26pitch%3D-1.5"
    url = (
        "https://www.google.com/maps/place/data="
        f"!3m8!1e1!3m6!1shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%3F{qs}!7i16384!8i8192"
    )
    pano_id, yaw, pitch, fov, mode_token = extract_from_maps_url(url)
    assert pano_id == "TESTPANO"
    assert pytest.approx(yaw, rel=1e-6) == 123.45
    assert pytest.approx(pitch, rel=1e-6) == -1.5
    assert fov is None  # No FOV in this URL
    assert mode_token is None  # No mode token in this URL


def test_extract_from_maps_url_pano_fallback():
    url = "https://www.google.com/maps/place/data=!3m5!1sPANO123!2e0"
    pano_id, yaw, pitch, fov, mode_token = extract_from_maps_url(url)
    assert pano_id == "PANO123"
    assert yaw is None and pitch is None
    assert fov is None
    assert mode_token is None


def test_metadata_to_dict_roundtrip():
    data = {
        "panoId": "ABC",
        "imageWidth": 16384,
        "imageHeight": 8192,
        "tileWidth": 512,
        "tileHeight": 512,
        "lat": 34.0,
        "lng": -118.0,
        "date": "2020-01",
        "copyright": "From the Owner, Google",
    }
    md = StreetViewMetadata.from_api_response(data)
    d = md.to_dict()
    assert d["pano_id"] == "ABC"
    assert d["image_width"] == 16384
    assert d["image_height"] == 8192
    assert d["tile_width"] == 512
    assert d["tile_height"] == 512


def test_extract_url_with_fov_and_mode_token():
    """Test extraction of FOV and mode token from URL."""
    url = "https://www.google.com/maps/@34.0385329,-118.2281272,3a,75y,358.11h,95.94t/data=!3m8!1e1"
    pano_id, yaw, pitch, fov, mode_token = extract_from_maps_url(url)
    assert fov == 75.0
    assert mode_token == "3a"
    # No pano_id in this URL format
    assert pano_id is None


def test_enhanced_metadata_fields():
    """Test that enhanced metadata fields are properly extracted."""
    data = {
        "panoId": "TEST123",
        "imageWidth": 13312,
        "imageHeight": 6656,
        "tileWidth": 512,
        "tileHeight": 512,
        "lat": 37.420864,
        "lng": -122.084465,
        "originalLat": 37.420800,
        "originalLng": -122.084400,
        "originalElevationAboveEgm96": 15.5,
        "heading": 94.35,
        "tilt": 88.39652,
        "roll": 1.7181772,
        "imageryType": "outdoor",
        "date": "2023-01",
        "copyright": "© 2023 Google",
        "reportProblemLink": "https://cbks0.googleapis.com/cbk?output=report&panoid=TEST123",
        "addressComponents": [
            {
                "longName": "United States",
                "shortName": "US",
                "types": ["country"]
            }
        ],
        "links": [
            {
                "panoId": "LINKED123",
                "heading": 274.48,
                "text": "Main St"
            }
        ]
    }
    
    md = StreetViewMetadata.from_api_response(data)
    d = md.to_dict()
    
    # Test new fields
    assert d["original_lat"] == 37.420800
    assert d["original_lng"] == -122.084400
    assert d["original_elevation_above_egm96"] == 15.5
    assert d["heading"] == 94.35
    assert d["tilt"] == 88.39652
    assert d["roll"] == 1.7181772
    assert d["imagery_type"] == "outdoor"
    assert d["report_problem_link"] == "https://cbks0.googleapis.com/cbk?output=report&panoid=TEST123"
    assert d["address_components"] is not None
    assert len(d["address_components"]) == 1
    assert d["address_components"][0]["longName"] == "United States"

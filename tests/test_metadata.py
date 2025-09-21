import pytest

from streetview_dl.metadata import extract_from_maps_url, validate_maps_url, StreetViewMetadata


def test_validate_maps_url_true():
    url = "https://www.google.com/maps/@?api=1&map_action=pano&parameters"  # contains markers
    assert validate_maps_url(url) is True


def test_validate_maps_url_false():
    assert validate_maps_url("https://example.com/") is False


def test_extract_from_maps_url_thumbnail_query():
    # Minimal synthetic URL including an encoded thumbnail query with panoid, yaw, pitch
    qs = "panoid%3DTESTPANO%26yaw%3D123.45%26pitch%3D-1.5"
    url = f"https://www.google.com/maps/place/data=!3m8!1e1!3m6!1shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%3F{qs}!7i16384!8i8192"
    pano_id, yaw, pitch = extract_from_maps_url(url)
    assert pano_id == "TESTPANO"
    assert pytest.approx(yaw, rel=1e-6) == 123.45
    assert pytest.approx(pitch, rel=1e-6) == -1.5


def test_extract_from_maps_url_pano_fallback():
    url = "https://www.google.com/maps/place/data=!3m5!1sPANO123!2e0"
    pano_id, yaw, pitch = extract_from_maps_url(url)
    assert pano_id == "PANO123"
    assert yaw is None and pitch is None


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


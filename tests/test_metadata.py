from unittest.mock import patch

import pytest
from click.testing import CliRunner

from streetview_dl.cli import main
from streetview_dl.metadata import (
    extract_from_maps_url,
    validate_maps_url,
    StreetViewMetadata,
)


EARTH_URL = (
    "https://earth.google.com/web/@38.58513623,68.7868674,846.01448556a,"
    "0d,90y,307.64599261h,85.13773982t,0r/data="
    "CgRCAggBIhoKFkNJSE0wb2dLRUlDQWdJRDQxdWI3S0EQBTIpCicKJQoh"
    "MWNfVG5OTklZdno4c0IzZThQTm5ON3R5XzVRX29qTXpUIAE6AwoBMEICCABKBwiVseMaEAE"
    "?utm_source=earthpro&utm_medium=product&utm_campaign=oct26"
    "&utm_content=launch_earth&authuser=0"
)

MAPS_URL = (
    "https://www.google.com/maps/@38.5851631,68.7868195,3a,75y,70.3h,99.32t/"
    "data=!3m8!1e1!3m6!1sCIABIhADydER5C1nfmfyqToADS0P!2e10!3e11!6s"
    "https:%2F%2Flh3.googleusercontent.com%2Fgpms-cs-s%2F"
    "AM4Q-U_sVsh7TAPS8icq5PMf_Cqg5P04akCa-XHfPpPT4ded7Q9a5kuIIrmUd-PQ2-"
    "lg7a8EUMFCGDIqGIgQEgGzbTpNp1fjGqyx_c_O7oRbG-1kZCu75nsNgl4XKCDR9Wzuot-f8EQ2G7Ij9ZaG"
    "%3Dw900-h600-k-no-pi-9.316254590464311-ya70.30424343540929-ro0-fo100"
    "!7i3584!8i1792?entry=ttu&g_ep=EgoyMDI2MTExMC4wIKXMDSoASAFQAw%3D%3D"
)


def test_extract_from_maps_url_contributed_photo():
    assert validate_maps_url(MAPS_URL) is True
    assert extract_from_maps_url(MAPS_URL) == (
        "CIABIhADydER5C1nfmfyqToADS0P", 70.3, 99.32, 75.0, "3a", None
    )


def test_extract_from_earth_url():
    assert validate_maps_url(EARTH_URL) is True
    pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(EARTH_URL)
    assert pano_id == "CIHM0ogKEICAgID41ub7KA"
    assert yaw == pytest.approx(307.64599261)
    assert pitch == pytest.approx(85.13773982)
    assert fov == 90.0
    assert mode_token == "0d"
    assert url_date is None


@pytest.mark.parametrize("data", ["", "%%%", "A", "CgRCAggB", "IhoKFkNJ", "IoA="])
def test_invalid_earth_data(data):
    url = f"https://earth.google.com/web/@1,2,100a,0d,90y/data={data}"
    assert validate_maps_url(url) is False
    assert extract_from_maps_url(url)[0] is None


def test_earth_url_without_street_view():
    assert validate_maps_url("https://earth.google.com/web/@1,2,100a") is False
    assert validate_maps_url(EARTH_URL.replace("earth.google.com", "example.com")) is False
    assert validate_maps_url(EARTH_URL.replace("earth.google.com", "earth.google.com.example.com")) is False


@pytest.mark.parametrize(
    "url,pano_id,yaw,mode_token",
    [
        (EARTH_URL, "CIHM0ogKEICAgID41ub7KA", 307.64599261, "0d"),
        (MAPS_URL, "CIABIhADydER5C1nfmfyqToADS0P", 70.3, "3a"),
    ],
)
def test_street_view_url_metadata_cli(tmp_path, url, pano_id, yaw, mode_token):
    metadata = StreetViewMetadata(
        pano_id=pano_id,
        image_width=12000,
        image_height=6000,
        tile_width=512,
        tile_height=512,
    )
    output = tmp_path / "metadata.json"
    with patch("streetview_dl.cli.get_api_key", return_value="test_key"), patch(
        "streetview_dl.cli.validate_api_key", return_value=True
    ), patch("streetview_dl.cli.StreetViewDownloader") as downloader_class:
        downloader = downloader_class.return_value
        downloader.get_metadata.return_value = metadata
        result = CliRunner().invoke(
            main, [url, "--metadata-only", "--output", str(output)]
        )

    assert result.exit_code == 0, result.output
    downloader.get_metadata.assert_called_once_with(pano_id=pano_id)
    downloader.download_panorama.assert_not_called()
    assert output.exists()
    assert metadata.url_yaw == pytest.approx(yaw)
    assert metadata.url_mode_token == mode_token


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
    pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(url)
    assert pano_id == "TESTPANO"
    assert pytest.approx(yaw, rel=1e-6) == 123.45
    assert pytest.approx(pitch, rel=1e-6) == -1.5
    assert fov is None  # No FOV in this URL
    assert mode_token is None  # No mode token in this URL
    assert url_date is None  # No date in this test URL


def test_extract_from_maps_url_pano_fallback():
    url = "https://www.google.com/maps/place/data=!3m5!1sPANO123!2e0"
    pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(url)
    assert pano_id == "PANO123"
    assert yaw is None and pitch is None
    assert fov is None
    assert mode_token is None
    assert url_date is None


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
    pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(url)
    assert fov == 75.0
    assert mode_token == "3a"
    assert pytest.approx(yaw, rel=1e-6) == 358.11
    assert pytest.approx(pitch, rel=1e-6) == 95.94
    # No pano_id in this URL format
    assert pano_id is None
    assert url_date is None


def test_extract_url_with_date():
    """Test extraction of date from URL."""
    url = "https://www.google.com/maps/@33.9966748,-118.4354761,3a,75y,64.64h,86.5t/data=!3m8!1e1!3m6!1sctFnHqFVrVUHPGX5eiV_lA!2e0!5s20221201T000000!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.4953573936320765%26panoid%3DctFnHqFVrVUHPGX5eiV_lA%26yaw%3D64.63771863471933!7i16384!8i8192?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSoASAFQAw%3D%3D"
    pano_id, yaw, pitch, fov, mode_token, url_date = extract_from_maps_url(url)
    assert pano_id == "ctFnHqFVrVUHPGX5eiV_lA"
    assert url_date == "20221201T000000"
    assert fov == 75.0
    assert mode_token == "3a"


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

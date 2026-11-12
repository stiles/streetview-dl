import json
from unittest.mock import Mock, patch

import pytest
import requests
from click.testing import CliRunner
from PIL import Image

from streetview_dl.cli import main
from streetview_dl.core import StreetViewDownloader
from streetview_dl.metadata import StreetViewMetadata


@pytest.mark.parametrize(
    "web_id,api_id,status,reason,width,height",
    [
        (
            "CIABIhADydER5C1nfmfyqToADS0P",
            "CAoSHENJQUJJaEFEeWRFUjVDMW5mbWZ5cVRvQURTMFA.",
            400, "invalidRequest", 3584, 1792,
        ),
        (
            "CIHM0ogKEICAgID4g_vSAQ",
            "CAoSFkNJSE0wb2dLRUlDQWdJRDRnX3ZTQVE.",
            404, "notFound", 10240, 5120,
        ),
    ],
)
def test_metadata_retries_web_photo_id_using_api_format(
    web_id, api_id, status, reason, width, height
):
    downloader = StreetViewDownloader(api_key="test-key")
    downloader._session_cache = "test-session"
    rejected = requests.Response()
    rejected.status_code = status
    rejected._content = json.dumps({
        "error": {"message": "Rejected", "errors": [{"reason": reason}]}
    }).encode()
    accepted = requests.Response()
    accepted.status_code = 200
    accepted._content = json.dumps({
        "panoId": api_id,
        "imageWidth": width,
        "imageHeight": height,
        "tileWidth": 512,
        "tileHeight": 512,
    }).encode()
    downloader._http = Mock()
    downloader._http.get.side_effect = [rejected, accepted]

    metadata = downloader.get_metadata(pano_id=web_id)

    assert metadata.pano_id == api_id
    assert metadata.image_width == width
    assert metadata.image_height == height
    calls = downloader._http.get.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["params"]["panoId"] == web_id
    assert calls[1].kwargs["params"]["panoId"] == api_id
    assert calls[0].kwargs["params"]["session"] == "test-session"
    assert calls[1].kwargs["params"]["session"] == "test-session"


@pytest.mark.parametrize(
    "status,pano_id,reason",
    [
        (403, "CIABIhADydER5C1nfmfyqToADS0P", "forbidden"),
        (400, "CIABIhADydER5C1nfmfyqToADS0P", "invalidKey"),
        (400, "CAoSHENJQUJJaEFEeWRFUjVDMW5mbWZ5cVRvQURTMFA.", "invalidRequest"),
        (400, "regular-pano-id", "invalidRequest"),
        (404, "regular-pano-id", "notFound"),
        (404, "CAoSFkNJSE0wb2dLRUlDQWdJRDRnX3ZTQVE.", "notFound"),
    ],
)
def test_metadata_does_not_retry_unrelated_errors(status, pano_id, reason):
    downloader = StreetViewDownloader(api_key="test-key")
    downloader._session_cache = "test-session"
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps({
        "error": {"message": "Rejected", "errors": [{"reason": reason}]}
    }).encode()
    downloader._http = Mock()
    downloader._http.get.return_value = response

    with pytest.raises(requests.HTTPError):
        downloader.get_metadata(pano_id=pano_id)

    downloader._http.get.assert_called_once()


@pytest.mark.parametrize(
    "quality,zoom,dimensions,tile_count",
    [
        ("high", 3, (3584, 1792), 28),
        ("medium", 2, (1792, 896), 8),
        ("low", 1, (896, 448), 2),
    ],
)
def test_small_panorama_uses_available_zoom(quality, zoom, dimensions, tile_count):
    downloader = StreetViewDownloader(api_key="test-key")
    downloader._session_cache = "test-session"
    metadata = StreetViewMetadata(
        pano_id="api-pano", image_width=3584, image_height=1792,
        tile_width=512, tile_height=512,
    )

    def fetch_tile(session, pano_id, z, x, y):
        assert z == zoom
        return Image.new("RGB", (512, 512), (120, 80, 40))

    with patch.object(downloader, "fetch_tile", side_effect=fetch_tile) as fetch:
        image = downloader.download_panorama(metadata, quality, concurrency=1)

    assert image.size == dimensions
    assert image.getpixel((dimensions[0] - 1, dimensions[1] - 1)) == (120, 80, 40)
    assert fetch.call_count == tile_count


def test_failed_tile_aborts_download_instead_of_returning_black_image():
    downloader = StreetViewDownloader(api_key="test-key")
    downloader._session_cache = "test-session"
    metadata = StreetViewMetadata(
        pano_id="api-pano", image_width=1024, image_height=512,
        tile_width=512, tile_height=512,
    )
    with patch.object(downloader, "fetch_tile", side_effect=requests.HTTPError("Tile failed")):
        with pytest.raises(requests.HTTPError, match="Tile failed"):
            downloader.download_panorama(metadata, "high", concurrency=1)


@pytest.mark.parametrize("operation", ["session", "metadata", "tile"])
def test_api_permission_error_is_actionable_and_redacts_key(operation):
    key = "test-api-key-must-not-appear"
    downloader = StreetViewDownloader(api_key=key)
    response = requests.Response()
    response.status_code = 403
    response.url = f"https://tile.googleapis.com/v1/createSession?key={key}"
    response._content = json.dumps({
        "error": {
            "status": "PERMISSION_DENIED",
            "message": f"Permission denied on the service. key={key}",
            "details": [{
                "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                "reason": "ACCESS_DENIED",
            }],
        }
    }).encode()
    downloader._http = Mock()
    downloader._http.post.return_value = response
    downloader._http.get.return_value = response

    with pytest.raises(requests.HTTPError) as exc:
        if operation == "session":
            downloader.create_session()
        elif operation == "metadata":
            downloader._session_cache = "test-session"
            downloader.get_metadata(pano_id="test-pano")
        else:
            downloader.fetch_tile("test-session", "test-pano", 3, 0, 0)

    message = str(exc.value)
    assert "403" in message
    assert "ACCESS_DENIED" in message
    assert "Permission denied on the service" in message
    assert "Map Tiles API" in message
    assert "billing" in message
    assert key not in message
    assert exc.value.response is response
    if operation == "session":
        assert downloader._session_cache is None


@pytest.mark.parametrize("body", [b"Forbidden", b'{"error": null}', b'[]'])
def test_nonstandard_api_error_does_not_expose_request_url(body):
    key = "test-api-key-must-not-appear"
    downloader = StreetViewDownloader(api_key=key)
    response = requests.Response()
    response.status_code = 403
    response.url = f"https://tile.googleapis.com/v1/createSession?key={key}"
    response._content = body
    downloader._http = Mock()
    downloader._http.post.return_value = response

    with pytest.raises(requests.HTTPError) as exc:
        downloader.create_session()

    assert "403" in str(exc.value)
    assert key not in str(exc.value)
    assert downloader._session_cache is None


def test_create_session_success_is_cached():
    downloader = StreetViewDownloader(api_key="test-key")
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"session": "test-session"}'
    downloader._http = Mock()
    downloader._http.post.return_value = response

    assert downloader.create_session() == "test-session"
    assert downloader.create_session() == "test-session"
    downloader._http.post.assert_called_once()


@pytest.mark.parametrize("endpoint", ["createSession", "streetview/metadata"])
def test_bad_request_identifies_endpoint_without_query_secrets(endpoint):
    key = "test-key-not-for-output"
    downloader = StreetViewDownloader(api_key=key)
    response = requests.Response()
    response.status_code = 400
    response.url = (
        f"https://tile.googleapis.com/v1/{endpoint}"
        f"?key={key}&session=private-session&panoId=TEST"
    )
    response._content = b'{"error":{"code":400,"message":"Bad Request"}}'

    with pytest.raises(requests.HTTPError) as exc:
        downloader._raise_for_api_error(response)

    message = str(exc.value)
    assert f"/v1/{endpoint}" in message
    assert "HTTP 400" in message
    assert "Bad Request" in message
    assert key not in message
    assert "private-session" not in message
    assert "?" not in message


def test_legacy_api_error_includes_reason_and_parameter():
    downloader = StreetViewDownloader(api_key="test-key")
    response = requests.Response()
    response.status_code = 400
    response.url = "https://tile.googleapis.com/v1/streetview/metadata"
    response._content = json.dumps({
        "error": {
            "message": "Bad Request",
            "errors": [{
                "reason": "badRequest",
                "message": "Invalid panorama identifier",
                "location": "panoId",
            }],
        }
    }).encode()

    with pytest.raises(requests.HTTPError) as exc:
        downloader._raise_for_api_error(response)

    message = str(exc.value)
    assert "badRequest" in message
    assert "Invalid panorama identifier" in message
    assert "panoId" in message


@pytest.mark.parametrize("verbose", [False, True])
def test_cli_http_error_does_not_expose_key_even_in_traceback(verbose):
    key = "AIza" + "x" * 35
    response = requests.Response()
    response.status_code = 403
    response.url = f"https://tile.googleapis.com/v1/createSession?key={key}"
    response._content = b'{"error":{"message":"Permission denied on the service."}}'
    http = Mock()
    http.post.return_value = response
    url = "https://www.google.com/maps/@1,2,3a,75y,70h,99t/data=!3m6!1sTEST!2e10"
    args = [url, "--api-key", key, "--metadata-only"]
    if verbose:
        args.append("--verbose")

    with patch.object(StreetViewDownloader, "_build_session", return_value=http):
        result = CliRunner().invoke(main, args)

    assert result.exit_code == 1
    assert "Permission denied on the service" in " ".join(result.output.split())
    assert "Map Tiles API" in result.output
    assert key not in result.output

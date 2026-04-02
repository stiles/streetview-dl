from click.testing import CliRunner
from unittest.mock import Mock, patch

from streetview_dl.cli import main, query_command, cli_dispatcher


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "streetview-dl" in result.output


def test_cli_accent_option_present():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert "--accent-color" in result.output


def test_query_command_help():
    """Test that query command help is accessible."""
    runner = CliRunner()
    result = runner.invoke(query_command, ["--help"])
    assert result.exit_code == 0
    assert "Query Street View panoramas by coordinates" in result.output
    assert "--lat" in result.output
    assert "--lng" in result.output
    assert "--radius" in result.output


def test_query_command_missing_lat():
    """Test that query command requires lat parameter."""
    runner = CliRunner()
    result = runner.invoke(query_command, ["--lng", "-118.25"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_query_command_missing_lng():
    """Test that query command requires lng parameter."""
    runner = CliRunner()
    result = runner.invoke(query_command, ["--lat", "34.05"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@patch('streetview_dl.cli.get_api_key')
@patch('streetview_dl.cli.validate_api_key')
@patch('streetview_dl.cli.StreetViewDownloader')
def test_query_command_basic(mock_downloader_class, mock_validate, mock_get_key):
    """Test basic query command functionality with mocked API."""
    # Setup mocks
    mock_get_key.return_value = "test_api_key"
    mock_validate.return_value = True
    
    # Create mock metadata
    mock_metadata = Mock()
    mock_metadata.pano_id = "test_pano_123"
    mock_metadata.date = "2025-10"
    mock_metadata.lat = 34.049958
    mock_metadata.lng = -118.250025
    mock_metadata.heading = 127.9
    mock_metadata.copyright_info = "Google"
    mock_metadata.links = []
    
    # Setup mock downloader instance
    mock_downloader = Mock()
    mock_downloader.get_metadata.return_value = mock_metadata
    mock_downloader_class.return_value = mock_downloader
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(query_command, [
        "--lat", "34.05",
        "--lng", "-118.25",
        "--radius", "50"
    ])
    
    assert result.exit_code == 0
    assert "test_pano_123" in result.output
    assert "2025-10" in result.output
    assert "Distance" in result.output


@patch('streetview_dl.cli.get_api_key')
@patch('streetview_dl.cli.validate_api_key')
@patch('streetview_dl.cli.StreetViewDownloader')
def test_query_command_json_output(mock_downloader_class, mock_validate, mock_get_key):
    """Test query command with JSON output."""
    import json
    
    # Setup mocks
    mock_get_key.return_value = "test_api_key"
    mock_validate.return_value = True
    
    # Create mock metadata
    mock_metadata = Mock()
    mock_metadata.pano_id = "test_pano_456"
    mock_metadata.date = "2025-10"
    mock_metadata.lat = 34.049958
    mock_metadata.lng = -118.250025
    mock_metadata.heading = 127.9
    mock_metadata.copyright_info = "Google"
    mock_metadata.links = []
    
    # Setup mock downloader instance
    mock_downloader = Mock()
    mock_downloader.get_metadata.return_value = mock_metadata
    mock_downloader_class.return_value = mock_downloader
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(query_command, [
        "--lat", "34.05",
        "--lng", "-118.25",
        "--json"
    ])
    
    assert result.exit_code == 0
    
    # Parse JSON output
    output_data = json.loads(result.output)
    assert "query" in output_data
    assert output_data["query"]["lat"] == 34.05
    assert output_data["query"]["lng"] == -118.25
    assert "panoramas" in output_data
    assert len(output_data["panoramas"]) > 0
    assert output_data["panoramas"][0]["pano_id"] == "test_pano_456"


@patch('streetview_dl.cli.get_api_key')
@patch('streetview_dl.cli.validate_api_key')
@patch('streetview_dl.cli.StreetViewDownloader')
def test_query_command_no_results(mock_downloader_class, mock_validate, mock_get_key):
    """Test query command when no panoramas are found."""
    # Setup mocks
    mock_get_key.return_value = "test_api_key"
    mock_validate.return_value = True
    
    # Setup mock downloader that raises exception (no panoramas found)
    mock_downloader = Mock()
    mock_downloader.get_metadata.side_effect = Exception("No panorama found")
    mock_downloader_class.return_value = mock_downloader
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(query_command, [
        "--lat", "0.0",
        "--lng", "0.0",
    ])
    
    assert result.exit_code == 1
    assert "No panoramas found" in result.output or "Query failed" in result.output

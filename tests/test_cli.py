from click.testing import CliRunner

from streetview_dl.cli import main


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

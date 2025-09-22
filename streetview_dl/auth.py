"""Authentication and API key management."""

import json
import os
from pathlib import Path
from typing import Optional

import click


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    config_dir = Path.home() / ".streetview-dl"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        click.echo(f"Warning: Could not save config: {e}", err=True)


def get_api_key(cli_key: Optional[str] = None) -> str:
    """
    Get API key from various sources in order of priority:
    1. CLI argument
    2. Environment variable
    3. Config file
    4. Interactive prompt
    """
    # 1. CLI argument has highest priority
    if cli_key:
        return cli_key

    # 2. Environment variable
    env_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if env_key:
        return env_key

    # 3. Config file
    config = load_config()
    config_key = config.get("api_key")
    if config_key:
        return config_key

    # 4. Interactive prompt
    return prompt_for_api_key()


def prompt_for_api_key() -> str:
    """Prompt user for API key and optionally save it."""
    click.echo()
    click.echo("Google Maps API key is required.")
    click.echo("Get one at: https://console.cloud.google.com/")
    click.echo("Make sure to enable the 'Map Tiles API'.")
    click.echo()

    api_key = click.prompt("Enter your Google Maps API key", hide_input=True)

    if click.confirm("Save this API key for future use?", default=True):
        config = load_config()
        config["api_key"] = api_key
        save_config(config)
        click.echo(f"API key saved to {get_config_path()}")

    return api_key


def configure_api_key() -> None:
    """Interactive configuration of API key."""
    config = load_config()
    current_key = config.get("api_key")

    if current_key:
        click.echo(f"Current API key: {current_key[:8]}...{current_key[-4:]}")
        if not click.confirm("Replace with a new key?"):
            return

    new_key = click.prompt("Enter your Google Maps API key", hide_input=True)

    config["api_key"] = new_key
    save_config(config)
    click.echo(f"API key saved to {get_config_path()}")


def validate_api_key(api_key: str) -> bool:
    """Basic validation of API key format."""
    if not api_key:
        return False

    # Google API keys are typically 39 characters starting with "AIza"
    if len(api_key) < 30 or not api_key.startswith("AIza"):
        return False

    return True

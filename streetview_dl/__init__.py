"""
streetview-dl: Download high-resolution Google Street View panoramas from the command line.

A free alternative to expensive commercial tools, built on Google's official Map Tiles API.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core import StreetViewDownloader
from .metadata import extract_from_maps_url, StreetViewMetadata

__all__ = ["StreetViewDownloader", "extract_from_maps_url", "StreetViewMetadata"]

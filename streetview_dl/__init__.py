"""
streetview-dl: Download high-resolution Google Street View panoramas from the command line.

A free alternative to expensive commercial tools, built on Google's official Map Tiles API.
"""

__version__ = "0.2.0"
__author__ = "Matt Stiles"
__email__ = "mattstiles@gmail.com"

from .core import StreetViewDownloader
from .metadata import extract_from_maps_url, StreetViewMetadata

__all__ = ["StreetViewDownloader", "extract_from_maps_url", "StreetViewMetadata"]

# Changelog

All notable changes to streetview-dl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for next release
- Comprehensive test suite
- CI/CD pipeline setup
- PyPI package publication
- Performance optimizations
- Additional image filters

## [0.1.0] - 2025-09-20 (Initial Release)

### Added
- Complete CLI interface with Click framework
- Rich terminal output with progress bars
- Support for Google Maps Street View URLs
- Multiple authentication methods (CLI, env vars, config file)
- Three quality levels (high/medium/low) for different file sizes
- Image filters: black & white, sepia, vintage
- Brightness, contrast, and saturation adjustments
- Comprehensive metadata extraction and JSON export
- Batch processing from URL files
- 360° XMP metadata embedding for photo viewers
- Multiple output formats (JPEG, PNG, WebP)
- Interactive API key configuration
- Verbose logging and error handling
- Professional package structure with pyproject.toml
- PyPI publishing workflow

## [0.0.1] - 2025-09-20 (Development)

### Added
- Core proof-of-concept script (`fetch_pano.py`)
- Google Map Tiles API integration
- Panorama tile downloading and stitching
- Basic XMP metadata embedding
- URL parsing for panorama ID extraction

### Changed
- Converted from standalone script to full Python package
- Refactored code into modular architecture
- Enhanced error handling and user experience

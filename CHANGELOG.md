# Changelog

All notable changes to streetview-dl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-09-21

### Added
- Auto-tuned concurrency for tile downloads (`--concurrency 0`) and manual override
- Parallel tile downloads with bounded workers
- Configurable HTTP resiliency: `--retries`, `--backoff` (also via env vars)
- Accent color option for terminal output (`--accent-color`)
- Grouped status spinners and end-of-run summary block
- Framing controls: `--fov`, `--clip left|right`, and `--crop-bottom <fraction>`
- True sepia filter using color matrix; vintage built on top
- Initial pytest suite (URL parsing, processing, CLI)
- GitHub Actions CI (lint, mypy, tests, build) with artifacts
- README examples, including Venice framing comparison

### Changed
- More informative URL validation (supports `map_action=pano` and `panoid=`)
- Rich output readability improvements

### Fixed
- Minor robustness in metadata parsing and downloader session handling

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

## [0.0.1] - 2025-09-20 (dev)

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

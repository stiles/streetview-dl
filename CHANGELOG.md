# Changelog

All notable changes to streetview-dl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-04-02

### Added
- **Coordinate query command**: New `query` subcommand to discover panoramas by lat/lng
- **Automatic URL generation**: Query command creates ready-to-use URL files for batch downloads
- **Grid-based sampling**: Systematic search grid to find disconnected clusters
- **Multi-strategy discovery**: Progressive radius, grid search, and deep link traversal
- **Distance calculation**: Returns distance in meters from query point to each panorama
- **JSON output mode**: `--json` flag for scripting and workflow automation
- **Advanced search parameters**: `--depth`, `--max-panos`, `--radius`, `--max-results` options
- **Auto-tuned depth**: Automatically adjusts traversal depth based on max-results

### Technical Details
- Added `query` command with three discovery strategies:
  1. Progressive radius search (1x, 2x, 3x, 5x)
  2. Grid-based search at multiple offset points
  3. Breadth-first link traversal up to depth 5
- Automatic generation of `streetview_urls_{lat}_{lng}.txt` files with valid URLs
- Uses haversine formula for accurate distance calculations  
- CLI dispatcher routes between download and query commands
- Results sorted by distance from query point
- Comprehensive test coverage with 6 new query tests

### Performance
- Alcatraz Island (27 acres): Discovers 150 panoramas in ~23 seconds
- Default settings (depth=auto, max-panos=200): ~20-40 API calls
- Aggressive settings (depth=5, max-panos=1000): ~100-200 API calls

### Use Cases
- Create grids for systematic area coverage
- Sample panoramas along routes or boundaries  
- Automate Street View data collection workflows
- Build datasets for computer vision or mapping
- Discover coverage programmatically without manual URL collection

### Examples
- `examples/alcatraz_example.py` - Alcatraz Island coverage discovery
- `examples/grid_coverage.py` - Grid-based area sampling
- `examples/query_example.py` - Simple query → download workflow

## [0.6.1] - 2025-02-08

### Fixed
- **FOV cropping not applying**: Fix `--fov` cropping by extracting heading/pitch from Maps URL path tokens (`...h`/`...t`) so horizontal crop applies when `h` is present
- Root cause: `url_yaw` was often None because only thumbnail query params were parsed, not URL path tokens
- Behavior: For a medium pano (8192 px), `--fov 90` now properly yields ~2048 px width when URL includes heading

### Changed
- Enhanced URL parsing regex to allow end-of-segment markers (not just comma)
- Path-based heading (`...h`) and pitch (`...t`) now serve as fallbacks when thumbnail query lacks yaw/pitch
- Updated EXAMPLES.md to clarify `h`/`t` requirement and included those tokens in all FOV example URLs

### Technical Details
- Modified `extract_from_maps_url()` in `metadata.py` to parse heading/yaw and pitch/tilt tokens from URL path
- Regex patterns now match `(-?\d+(?:\.\d+)?)h(?:,|/|$)` and `(-?\d+(?:\.\d+)?)t(?:,|/|$)`
- Added test coverage for path-based yaw/pitch extraction

## [0.6.0] - 2025-10-21

### Added
- **Historical imagery discovery**: New `--historical` and `--historical-download` options
- **Date extraction from URLs**: Parse historical date parameters (e.g., `5s20221201T000000`)
- **Advanced discovery algorithm**: Deep link traversal and wider area searches to find historical panoramas
- **Automatic historical downloads**: Download all discoverable historical versions with date-stamped filenames
- **Enhanced metadata**: Added `url_date` field to capture date information from URLs
- **Historical examples**: Added Karate Kid apartment examples in `examples/historical-karate-kid-apartment/`

### Technical Details
- Extended `extract_from_maps_url()` to return 6 values instead of 5 (added date extraction)
- Added `discover_historical_dates()` method to `StreetViewDownloader` class
- Enhanced CLI with historical processing workflow and progress reporting
- Updated all function signatures and tests to handle new date parameter

### Limitations (v0.6.0 - improved in later versions)
- Historical discovery found ~40-60% of available dates with depth-2 traversal
- Cannot access Google's complete internal historical database
- Success rate varies by location and available linked panorama data

## [0.5.1] - 2025-10-18

### Fixed
- **Critical bug fix**: FOV parameter not working correctly due to variable name conflict
- **Default behavior**: Now defaults to full 360° panoramas when no `--fov` specified (was incorrectly using URL-extracted FOV)
- **CLI parameter precedence**: `--fov` parameter now properly overrides any FOV extracted from URLs

### Technical Details
- Fixed variable name conflict between CLI `fov` parameter and URL-extracted `fov` in `cli.py`
- Renamed URL-extracted variable to `url_fov` to prevent collision
- Corrected metadata assignment: `street_view_metadata.url_fov` now uses URL-extracted value, not CLI parameter

### Impact
- **Before**: `--fov 360` was ignored, always cropped to URL FOV (e.g., 75°)
- **After**: `--fov 360` works correctly, gives full panorama
- **Default behavior**: Full 360° panoramas (8192×3072) instead of narrow crops (1706×3072)

## [0.5.0] - 2025-10-17

### Added
- **Enhanced metadata extraction**: Complete implementation of all Google Street View Tile API metadata fields
- **Camera orientation data**: `heading`, `tilt`, and `roll` fields for 3D reconstruction and analysis
- **Original location data**: `original_lat`, `original_lng`, and `original_elevation_above_egm96` fields
- **Address components**: Structured address data with country, locality, route, and street number
- **Imagery classification**: `imagery_type` field indicating "indoor" or "outdoor" panoramas
- **Problem reporting**: `report_problem_link` field for quality control and issue reporting
- **Enhanced URL parsing**: Extract field of view (`url_fov`) and mode token (`url_mode_token`) from Google Maps URLs
- **Comprehensive test coverage**: New tests for enhanced metadata fields and URL parsing functionality

### Changed
- **Expanded metadata output**: `--metadata` and `--metadata-only` now extract 11 additional fields from the API
- **Enhanced URL parsing**: `extract_from_maps_url()` now returns 5 values instead of 3 (pano_id, yaw, pitch, fov, mode_token)
- **Improved documentation**: README updated with complete metadata field reference and descriptions

### Technical Details
- Extended `StreetViewMetadata` Pydantic model with new optional fields
- Updated `from_api_response()` method to extract all available API response fields
- Enhanced URL regex patterns to capture FOV (e.g., "75y") and mode tokens (e.g., "3a")
- Maintained full backward compatibility with existing metadata structure
- All existing functionality preserved without breaking changes

### Developer Benefits
- **Research applications**: Complete camera orientation and location data for spatial analysis
- **Content organization**: Enhanced metadata for panorama collection management
- **Quality control**: Problem reporting links and imagery type classification
- **Data science**: Rich metadata for machine learning datasets and geocoding applications

## [0.4.0] - 2025-09-27

### Added
- `--no-crop` convenience flag to disable default bottom cropping

### Changed
- **BREAKING**: Default behavior now crops bottom 25% of images to remove car blur and dashboard elements
- Images are automatically cropped to `--crop-bottom 0.75` by default (was 1.0)

### Migration Notes
- **v0.3.x behavior**: Use `--no-crop` or `--crop-bottom 1.0` to keep full image height
- **New default**: Bottom 25% is automatically removed unless overridden
- **Rationale**: Car blur and dashboard elements are rarely wanted in Street View panoramas

## [0.3.0] - 2025-09-27

### Added
- Comprehensive unit tests for image cropping functionality
- Field of view examples section in README
- Integration warning when combining `--fov` with `--clip` in potentially confusing ways
- EXAMPLES.md with detailed CLI usage examples, real command outputs, and embedded result images
- generate_examples.py script to create sample outputs for all major features
- Street View URL parameter documentation with visual breakdown diagram

### Changed
- **BREAKING**: Unified `--fov` and `--clip` processing for consistent behavior
- Improved coordinate system consistency between FOV and directional clipping
- Enhanced documentation with proper `--fov` option reference and examples
- Processing order: `--fov` and `--clip` now work together logically instead of sequentially

### Fixed
- Coordinate system inconsistency between `crop_fov()` and `--clip` implementation
- Incorrect half-width calculation in directional clipping (was `width // 4`, now properly calculated)
- Processing order issue where `--fov` and `--clip` could produce unexpected results when combined
- Missing documentation for `--fov` option in main options reference

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

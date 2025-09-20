# Street View Panorama Downloader - Project Planning

## Package Name
**`streetview-dl`** - Final choice (similar to youtube-dl pattern)

✅ **IMPLEMENTED** - Package structure complete and working

## Core Features

### 1. CLI Interface
```bash
# Basic usage
streetview-dl "https://www.google.com/maps/@33.99,-118.40,3a,75y,148h,98t/..."

# With options
streetview-dl --quality medium --format bw --output my-pano.jpg <url>

# Batch processing
streetview-dl --batch urls.txt --output-dir ./panoramas/

# Metadata only
streetview-dl --metadata-only <url>
```

### 2. Authentication Options (Priority Order)
1. CLI argument: `--api-key YOUR_KEY`
2. Environment variable: `GOOGLE_MAPS_API_KEY`
3. Config file: `~/.streetview-dl/config.json`
4. Interactive prompt (with option to save)

### 3. Output Quality/Size Options
- `--quality high|medium|low` (controls zoom level: 5,4,3)
- `--max-width 8192` (resize if larger)
- `--jpeg-quality 85` (compression level)
- `--format jpg|png|webp`

### 4. Image Processing
- `--filter bw|sepia|vintage|none`
- `--brightness 1.0` (adjustment factor)
- `--contrast 1.0` (adjustment factor)
- `--saturation 1.0` (adjustment factor)

### 5. Metadata Extraction
Extract and optionally save as JSON:
- Panorama ID
- Coordinates (lat/lng)
- Date captured
- Copyright info
- Image dimensions
- Heading/pitch from URL
- Nearby panorama links

### 6. Advanced Features
- Progress bars for large downloads
- Retry logic with exponential backoff
- Concurrent tile downloading
- Caching of sessions and metadata
- Validation of Google Maps URLs

## Project Structure
```
streetview-dl/
├── streetview_dl/
│   ├── __init__.py
│   ├── cli.py           # Main CLI interface
│   ├── core.py          # Core downloading logic
│   ├── auth.py          # API key management
│   ├── metadata.py      # URL parsing and metadata
│   ├── processing.py    # Image filters and processing
│   └── utils.py         # Utilities and helpers
├── tests/
├── docs/
├── scripts/
│   └── publish.sh       # PyPI publishing script
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Technical Decisions

### Dependencies
- **Click** - Modern CLI framework (better than argparse)
- **Requests** - HTTP client
- **Pillow** - Image processing
- **Rich** - Beautiful terminal output and progress bars
- **Pydantic** - Data validation and settings management

### Error Handling
- Graceful failures with helpful error messages
- Automatic retry for network issues
- Clear guidance when API key is invalid
- Fallback options when tiles are missing

### Configuration
```json
{
  "api_key": "your_key_here",
  "default_quality": "high",
  "default_output_dir": "./panoramas",
  "default_filter": "none",
  "concurrent_downloads": 4
}
```

## Development Phases

### Phase 1: Core Package ✅ COMPLETE
- [x] Working script (done)
- [x] Package structure
- [x] Basic CLI with Click
- [x] API key management
- [x] Quality options

### Phase 2: Enhanced Features ✅ COMPLETE
- [x] Image filters (BW, sepia, vintage)
- [x] Metadata extraction
- [x] Progress bars
- [x] Config file support
- [x] Brightness/contrast/saturation adjustments
- [x] Batch processing
- [x] Multiple output formats

### Phase 3: Polish & Distribution 🚧 IN PROGRESS
- [x] Documentation (README, CHANGELOG)
- [x] PyPI setup (publish script ready)
- [ ] Comprehensive tests
- [ ] CI/CD pipeline
- [ ] Official PyPI publication

## Success Metrics ✅ ACHIEVED
- ✅ Easy installation: `pip install -e .` (PyPI coming soon)
- ✅ Simple usage: `streetview-dl <url>`
- ✅ File sizes: 50-90% smaller with quality options (3.1MB vs 10MB+ tested)
- ✅ Speed: Downloads complete quickly with progress bars
- ✅ Reliability: Handles network issues and API limits gracefully
- ✅ Rich CLI: Beautiful terminal output with progress and status
- ✅ Metadata: Complete extraction of location, date, copyright, links

## Competitive Analysis
- **Street View Download 360**: $79, Windows only, no CLI
- **GSVDownloader**: Free but complex setup, research-focused
- **Our tool**: Free, cross-platform, simple CLI, open source

## Marketing Points 🎯
- ✅ "Free alternative to $79 commercial tools"
- ✅ "Built on official Google APIs"
- ✅ "Simple CLI for automation and scripting"
- ✅ "Full resolution panoramas with 360° metadata"
- ✅ "Flexible output formats and artistic processing"
- ✅ "Cross-platform Python package"
- ✅ "Batch processing and metadata extraction"
- ✅ "Professional terminal interface with progress bars"

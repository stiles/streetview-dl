# streetview-dl

Download high-resolution Google Street View panoramas from the command line.

## What it does

Converts Google Maps Street View URLs into full-resolution equirectangular panorama images. Downloads the raw tiles from Google's official Map Tiles API and stitches them together, preserving maximum quality and adding proper 360° metadata.

## Installation

```bash
# From PyPI (coming soon)
pip install streetview-dl

# From source (current)
git clone https://github.com/yourusername/streetview-dl
cd streetview-dl
pip install -e .
```

## Quick start

```bash
# Basic download
streetview-dl "https://www.google.com/maps/@33.99,-118.40,3a,75y,148h,98t/..."

# Specify output file
streetview-dl --output beach-pano.jpg "https://maps.url..."

# Lower quality for smaller files
streetview-dl --quality medium "https://maps.url..."

# Black and white filter
streetview-dl --filter bw "https://maps.url..."
```

## Setup

### Get a Google Maps API key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the "Map Tiles API"
4. Create credentials → API Key
5. Set up billing (required for Map Tiles API)

### Configure authentication

Choose one method:

```bash
# Environment variable (recommended)
export GOOGLE_MAPS_API_KEY="your_api_key_here"

# CLI argument
streetview-dl --api-key "your_key" "https://maps.url..."

# Config file
streetview-dl --configure
```

## Options

### Quality and output
```bash
--quality high|medium|low    # Default: high (16K+ resolution)
--output filename.jpg        # Custom output filename
--format jpg|png|webp        # Image format (default: jpg)
--jpeg-quality 85            # JPEG compression (1-100)
--max-width 8192             # Resize if larger
```

### Image processing
```bash
--filter bw|sepia|vintage    # Apply artistic filters
--brightness 1.2             # Adjust brightness
--contrast 1.1               # Adjust contrast
--saturation 0.8             # Adjust color saturation
```

### Metadata and batch processing
```bash
--metadata                   # Save metadata as JSON
--metadata-only              # Extract metadata without downloading
--batch urls.txt             # Process multiple URLs
--output-dir ./panoramas/    # Output directory for batch
```

### Advanced
```bash
--no-xmp                     # Skip 360° metadata embedding
--timeout 30                 # Request timeout seconds
--configure                  # Configure API key interactively
--verbose                    # Verbose output
```

## Examples

### Basic usage
```bash
# Download full resolution panorama
streetview-dl "https://www.google.com/maps/@40.7589,-73.9851,3a,75y,200h,90t/data=..."
```

### Smaller file sizes
```bash
# Medium quality (~2-4MB instead of 10MB+)
streetview-dl --quality medium --jpeg-quality 75 "https://maps.url..."

# Low quality for thumbnails (~500KB)
streetview-dl --quality low --max-width 2048 "https://maps.url..."
```

### Artistic filters
```bash
# Black and white
streetview-dl --filter bw "https://maps.url..."

# Vintage sepia tone
streetview-dl --filter sepia --brightness 1.1 --contrast 0.9 "https://maps.url..."
```

### Batch processing
```bash
# Create urls.txt with one URL per line, then:
streetview-dl --batch urls.txt --output-dir ./my-panoramas/ --quality medium
```

### Metadata extraction
```bash
# Get location data, capture date, copyright info
streetview-dl --metadata-only "https://maps.url..."

# Save both image and metadata
streetview-dl --metadata "https://maps.url..."
```

## Output

Downloads create equirectangular panorama images with:
- Full resolution (typically 16384×8192 pixels)
- Proper XMP metadata for 360° photo viewers
- Geographic and temporal metadata when available
- Copyright and attribution information

Files are compatible with:
- Facebook 360° photos
- VR headsets and viewers
- Google Photos spherical view
- Any software supporting equirectangular panoramas

## API limits and costs

Uses Google's official Map Tiles API:
- Requires billing enabled (small cost per request)
- Subject to standard API quotas
- Much cheaper than commercial alternatives
- Respects Google's terms of service

## Requirements

- Python 3.8+
- Google Maps API key with Map Tiles API enabled
- Internet connection

## License

MIT License - see LICENSE file for details

## Development status

✅ **Fully functional** - All core features implemented and tested

- [x] CLI interface with rich terminal output
- [x] Multiple quality levels (high/medium/low)
- [x] Image filters (BW, sepia, vintage) with adjustments
- [x] Comprehensive metadata extraction
- [x] Batch processing capabilities
- [x] Multiple authentication methods
- [x] 360° XMP metadata embedding
- [x] Progress bars and error handling

## Contributing

Issues and pull requests welcome at the [GitHub repository](https://github.com/yourusername/streetview-dl).

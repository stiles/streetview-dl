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
--quality high|medium|low    # Default: medium (8K resolution, good balance)
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

### Quality options
```bash
# High quality for maximum detail (16K resolution, ~10MB)
streetview-dl --quality high "https://maps.url..."

# Default medium quality (8K resolution, ~4MB, good balance)
streetview-dl "https://maps.url..."

# Low quality for thumbnails (4K resolution, ~1MB)
streetview-dl --quality low "https://maps.url..."
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
streetview-dl --batch urls.txt --output-dir ./my-panoramas/
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
- Full resolution (typically 16384×8192 pixels with the "high" flag)
- Proper XMP metadata for 360° photo viewers
- Geographic and temporal metadata when available
- Copyright and attribution information

Files are compatible with:
- Facebook 360° photos
- VR headsets and viewers
- Google Photos spherical view
- Any software supporting equirectangular panoramas

## API limits and costs

Uses Google's official [Map Tiles API](https://developers.google.com/maps/documentation/tile):
- Requires billing enabled
- No charge for less than 100k requests per month
- **Quality impacts requests**: `high` = 512 tiles, `medium` = 128 tiles, `low` = 32 tiles
- Subject to standard API quotas
- Virtually free and cheaper than [commercial alternatives](https://svd360.com/)
- Respects Google's terms of service

## Requirements

- Python 3.8+
- Google Maps API key with Map Tiles API enabled

## License

[MIT License](LICENSE.md)

## Contributing

Issues and pull requests welcome at the [GitHub repository](https://github.com/stiles/streetview-dl).

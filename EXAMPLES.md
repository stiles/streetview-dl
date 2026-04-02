# streetview-dl Examples

This document provides comprehensive examples of `streetview-dl` usage with real commands and their outputs. All examples use the [same Venice Street View location](https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu) for consistency.

## Test Location

**[Venice, Italy — Cannaregio Canal](https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu)**
- **URL**: `https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=...` (includes `h` heading + `t` pitch tokens)
- **Coordinates**: 45.4360629, 12.3305426
- **Heading**: 236.1° (Southwest, from the URL `...h` token)
- **Pitch**: 86.64° (Looking slightly down, from the URL `...t` token)
- **Original FOV**: 60° (zoomed in view)

## Running the Examples

To generate all examples automatically:

```bash
python generate_examples.py
```

This will create an `examples/` directory with all the sample images.

## Basic Quality Options

### Low Quality (4K, ~1MB)
```bash
streetview-dl --quality low --output venice_low_quality.jpg "https://maps.url..."
```
- **Resolution**: ~4K (4096×2048)
- **File size**: ~1MB
- **Use case**: Thumbnails, previews, web display

![Low Quality](examples/venice_low_quality.jpg)

### Medium Quality (8K, ~4MB) - Default
```bash
streetview-dl --quality medium --output venice_medium_quality.jpg "https://maps.url..."
```
- **Resolution**: ~8K (8192×4096)
- **File size**: ~4MB
- **Use case**: Good balance of quality and size

![Medium Quality](examples/venice_medium_quality.jpg)

### High Quality (16K, ~10MB)
```bash
streetview-dl --quality high --output venice_high_quality.jpg "https://maps.url..."
```
- **Resolution**: ~16K (16384×8192)
- **File size**: ~10MB
- **Use case**: Maximum detail, printing, professional use

![High Quality](examples/venice_high_quality.jpg)

## Field of View Examples

The following FOV examples use a URL that includes both the `h` (heading) and `t` (pitch) tokens so the crop has a defined view center:

```text
https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu
```

### Narrow 90° View
```bash
streetview-dl --fov 90 --output venice_fov_90deg.jpg \
"https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu"
```
- **Use case**: Architectural details, focused composition
- **Result**: Crops to 90° around the URL's heading (236°)
- **Note**: FOV cropping uses the heading (`...h`) in the URL. If the URL lacks `h`, no horizontal crop is applied.

![90° FOV](examples/venice_fov_90deg.jpg)

### Standard 180° Half-Panorama
```bash
streetview-dl --fov 180 --output venice_fov_180deg.jpg \
"https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu"
```
- **Use case**: Standard wide-angle view
- **Result**: Half the full panorama width

![180° FOV](examples/venice_fov_180deg.jpg)

### Wide 270° View
```bash
streetview-dl --fov 270 --output venice_fov_270deg.jpg \
"https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu"
```
- **Use case**: Context, environmental documentation
- **Result**: Three-quarters of the full panorama

![270° FOV](examples/venice_fov_270deg.jpg)

## Directional Clipping

### Forward-Facing View
```bash
streetview-dl --clip right --output venice_clip_forward.jpg "https://maps.url..."
```
- **Result**: 180° centered on the URL's heading (236°)
- **Use case**: What the camera operator was facing

![Forward Clip](examples/venice_clip_forward.jpg)

### Rear-Facing View
```bash
streetview-dl --clip left --output venice_clip_rear.jpg "https://maps.url..."
```
- **Result**: 180° centered on the opposite direction (236° + 180° = 416° = 56°)
- **Use case**: What was behind the camera operator

![Rear Clip](examples/venice_clip_rear.jpg)

### Combined FOV + Clipping
```bash
streetview-dl --fov 220 --clip right --output venice_fov220_clip_forward.jpg "https://maps.url..."
```
- **Result**: Clipping overrides FOV, still produces 180° forward view
- **Note**: Shows warning about potentially unexpected results

![FOV + Clip](examples/venice_fov220_clip_forward.jpg)

## Image Filters

### Black and White
```bash
streetview-dl --filter bw --output venice_blackwhite.jpg "https://maps.url..."
```
- **Effect**: Converts to grayscale while maintaining RGB format
- **Use case**: Artistic effect, document scanning

![Black and White](examples/venice_blackwhite.jpg)

### Sepia Tone
```bash
streetview-dl --filter sepia --output venice_sepia.jpg "https://maps.url..."
```
- **Effect**: Warm brown tones using color matrix transformation
- **Use case**: Vintage aesthetic, historical documentation

![Sepia](examples/venice_sepia.jpg)

### Vintage Effect
```bash
streetview-dl --filter vintage --output venice_vintage.jpg "https://maps.url..."
```
- **Effect**: Sepia + reduced saturation + slight brightness boost
- **Use case**: Nostalgic mood, artistic projects

![Vintage](examples/venice_vintage.jpg)

## Image Adjustments

### Brightness Adjustment
```bash
streetview-dl --brightness 1.3 --output venice_bright.jpg "https://maps.url..."
```
- **Effect**: 30% brighter than original
- **Range**: 0.1 to 3.0 (0.1 = very dark, 3.0 = very bright)

![Brightness](examples/venice_bright.jpg)

### Contrast Enhancement
```bash
streetview-dl --contrast 1.4 --output venice_high_contrast.jpg "https://maps.url..."
```
- **Effect**: 40% more contrast
- **Range**: 0.1 to 3.0 (0.1 = flat, 3.0 = high contrast)

![High Contrast](examples/venice_high_contrast.jpg)

### Saturation Control
```bash
streetview-dl --saturation 0.6 --output venice_desaturated.jpg "https://maps.url..."
```
- **Effect**: 40% less color saturation
- **Range**: 0.0 to 3.0 (0.0 = grayscale, 3.0 = very saturated)

![Desaturated](examples/venice_desaturated.jpg)

## Cropping Options

### Default Behavior (NEW in v0.4.0)
By default, streetview-dl now removes the bottom 25% of images to eliminate car blur and dashboard elements.

```bash
# Default behavior - automatically crops bottom 25%
streetview-dl --output venice_default_crop.jpg "https://maps.url..."
```

### Custom Bottom Crop
```bash
streetview-dl --crop-bottom 0.75 --output venice_crop_bottom.jpg "https://maps.url..."
```
- **Effect**: Keeps top 75% of image height (same as default)
- **Use case**: Remove car dashboard, ground clutter, focus on horizon

![Bottom Crop](examples/venice_crop_bottom.jpg)

### Disable Cropping
```bash
streetview-dl --no-crop --output venice_no_crop.jpg "https://maps.url..."
```
- **Effect**: Keeps full image height (pre-v0.4.0 behavior)
- **Use case**: Research, VR applications, ground analysis

### Aggressive Cropping
```bash
streetview-dl --crop-bottom 0.6 --output venice_aggressive_crop.jpg "https://maps.url..."
```
- **Effect**: Keeps top 60% of image height
- **Use case**: Focus on horizon/sky, social media crops

## Output Formats

### PNG Format
```bash
streetview-dl --format png --output venice_format.png "https://maps.url..."
```
- **Use case**: Lossless compression, transparency support
- **File size**: Larger than JPEG

![PNG Format](examples/venice_format.png)

### WebP Format
```bash
streetview-dl --format webp --output venice_format.webp "https://maps.url..."
```
- **Use case**: Modern web format, good compression
- **File size**: Smaller than JPEG with similar quality

![WebP Format](examples/venice_format.webp)

### JPEG Quality Control
```bash
streetview-dl --format jpg --jpeg-quality 85 --output venice_quality85.jpg "https://maps.url..."
```
- **Range**: 1-100 (1 = smallest file/lowest quality, 100 = largest file/highest quality)
- **Default**: 92

## Size Control

### Maximum Width Limit
```bash
streetview-dl --quality high --max-width 4096 --output venice_max_width.jpg "https://maps.url..."
```
- **Effect**: Starts with high quality, then resizes if wider than 4096px
- **Use case**: Ensure compatibility with systems that have size limits

![Max Width](examples/venice_max_width.jpg)

## Metadata Options

### Download with Metadata
```bash
streetview-dl --metadata --output venice_with_metadata.jpg "https://maps.url..."
```
- **Result**: Creates both `venice_with_metadata.jpg` and `venice_with_metadata.json`
- **Metadata includes**: Location, date, copyright, camera parameters

![With Metadata](examples/venice_with_metadata.jpg)

### Metadata Only
```bash
streetview-dl --metadata-only "https://maps.url..."
```
- **Result**: Creates only the JSON metadata file, no image download
- **Use case**: Data collection, location verification

## Complex Combinations

### Professional Photography Setup
```bash
streetview-dl \
  --quality high \
  --fov 200 \
  --clip right \
  --crop-bottom 0.8 \
  --filter vintage \
  --brightness 1.1 \
  --contrast 1.2 \
  --format jpg \
  --jpeg-quality 95 \
  --metadata \
  --output venice_professional.jpg \
  "https://maps.url..."
```

This command demonstrates combining multiple options:
- High quality for maximum detail
- 200° FOV clipped to forward 180°
- Bottom crop to remove distractions
- Vintage filter for aesthetic
- Slight brightness and contrast boost
- High JPEG quality
- Include metadata for documentation

![Complex Example](examples/venice_complex.jpg)

### Web Optimization
```bash
streetview-dl \
  --quality medium \
  --fov 180 \
  --max-width 2048 \
  --format webp \
  --crop-bottom 0.85 \
  --output venice_web_optimized.webp \
  "https://maps.url..."
```

Optimized for web use:
- Medium quality for good size/quality balance
- Standard 180° view
- Width limit for fast loading
- WebP format for smaller files
- Light bottom crop for better composition

## Understanding the Results

### File Naming Convention

The `generate_examples.py` script creates files with descriptive names:
- `venice_low_quality.jpg` - Quality level
- `venice_fov_90deg.jpg` - Field of view setting
- `venice_clip_forward.jpg` - Clipping direction
- `venice_blackwhite.jpg` - Filter applied
- `venice_complex.jpg` - Multiple options combined

### Expected File Sizes

| Quality | Typical Size | Resolution |
|---------|-------------|------------|
| Low | 0.8-1.5 MB | ~4K |
| Medium | 3-5 MB | ~8K |
| High | 8-12 MB | ~16K |

*Actual sizes vary based on image content, filters, and compression settings.*

### Performance Notes

- **High quality**: Takes longer to download (512 tiles vs 32-128)
- **Complex filters**: Add processing time
- **Large FOV**: More image data to process
- **Multiple options**: Cumulative processing time

## Troubleshooting

### Common Issues

1. **"Invalid Google Maps Street View URL"**
   - Ensure the URL contains a panorama ID
   - Check that the URL isn't truncated

2. **"API key error"**
   - Set `GOOGLE_MAPS_API_KEY` environment variable
   - Ensure Map Tiles API is enabled in Google Cloud Console

3. **"--fov doesn't crop horizontally"**
   - Ensure the URL includes a heading token (e.g., `...,236.1h,...`)
   - Use the Street View share link (not the place URL) so `h` and `t` are present

4. **"No panorama data available"**
   - The panorama may have been removed or restricted
   - Try a different location

5. **Files larger than expected**
   - Use `--max-width` to limit dimensions
   - Lower `--jpeg-quality` for smaller files
   - Use `--quality low` for quick tests

### Getting Help

```bash
streetview-dl --help
streetview-dl query --help
streetview-dl --version
streetview-dl --verbose "https://maps.url..."  # Detailed output
```

## Coordinate Query Examples

The `query` command discovers Street View panoramas at any location using coordinates, enabling automation and grid-based sampling.

### Basic Location Query

```bash
streetview-dl query --lat 34.05 --lng -118.25
```

**Output:**
```
Searching for panoramas near (34.05, -118.25)...

Found 3 panorama(s):

1. _3y4YfZwv0K7mGHOYvCB6A
   Date: 2025-10
   Distance: 5.2m
   Coordinates: (34.049958, -118.250025)

2. TVwZqqQWoyxEhc1W3cmeUg
   Date: 2025-10
   Distance: 10.0m
   Coordinates: (34.050012, -118.250108)

3. RJ3Y_aMsHHX9WozS5xLBJA
   Date: 2025-10
   Distance: 11.9m
   Coordinates: (34.049904, -118.249943)

Download a panorama using:
  streetview-dl "https://www.google.com/maps/@34.049958,-118.250025,..."
```

### Wider Search Area

```bash
streetview-dl query --lat 40.7589 --lng -73.9851 --radius 100 --max-results 10
```

Search parameters:
- `--radius 100` - Search within 100 meters
- `--max-results 10` - Return up to 10 panoramas
- Results sorted by distance from query point

### JSON Output for Automation

```bash
streetview-dl query --lat 34.05 --lng -118.25 --json
```

**Output:**
```json
{
  "query": {
    "lat": 34.05,
    "lng": -118.25,
    "radius": 50
  },
  "count": 3,
  "panoramas": [
    {
      "pano_id": "_3y4YfZwv0K7mGHOYvCB6A",
      "date": "2025-10",
      "lat": 34.049958,
      "lng": -118.250025,
      "distance_m": 5.2,
      "heading": 127.9,
      "copyright": "From the Owner, Photo by: Google"
    }
  ]
}
```

### Complete Automation Workflow

**Streamlined approach (automatic URL file):**

```bash
# Query generates both human-readable output and URL file
streetview-dl query --lat 34.05 --lng -118.25 --max-results 10

# Download using the auto-generated URL file
streetview-dl --batch streetview_urls_34.05_-118.25.txt --output-dir ./panoramas/ --quality medium
```

**Advanced workflow with JSON and jq:**

```bash
# 1. Query for panoramas near a location
streetview-dl query --lat 34.05 --lng -118.25 --max-results 10 --json > results.json

# 2. Extract pano IDs and coordinates (using jq)
jq -r '.panoramas[] | 
  "https://www.google.com/maps/@\(.lat),\(.lng),3a,75y,0h,90t/data=!3m7!1e1!3m5!1s\(.pano_id)!"' \
  results.json > urls.txt

# 3. Batch download all panoramas
streetview-dl --batch urls.txt --output-dir ./panoramas/ --quality medium

# 4. Or download just the nearest one
NEAREST_URL=$(jq -r '.panoramas[0] | 
  "https://www.google.com/maps/@\(.lat),\(.lng),3a,75y,0h,90t/data=!3m7!1e1!3m5!1s\(.pano_id)!"' \
  results.json)
streetview-dl "$NEAREST_URL" --output nearest.jpg
```

### Python Integration Example

```python
import json
import subprocess

# Query for panoramas
result = subprocess.run(
    ["streetview-dl", "query",
     "--lat", "34.05",
     "--lng", "-118.25", 
     "--radius", "100",
     "--max-results", "10",
     "--json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Get nearest panorama
nearest = data['panoramas'][0]
print(f"Nearest panorama: {nearest['pano_id']}")
print(f"Distance: {nearest['distance_m']}m")
print(f"Date: {nearest['date']}")

# Build URL and download
url = (f"https://www.google.com/maps/@{nearest['lat']},{nearest['lng']},"
       f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{nearest['pano_id']}")

# Download the panorama
subprocess.run([
    "streetview-dl",
    "--quality", "medium",
    "--output", f"pano_{nearest['pano_id']}.jpg",
    url
])
```

### Grid Sampling Example

Create a grid of points and query each one:

```python
import json
import subprocess

# Define grid parameters
center_lat, center_lng = 34.05, -118.25
grid_size = 5  # 5x5 grid
spacing = 0.001  # ~100m spacing

panoramas = []

# Query each grid point
for i in range(grid_size):
    for j in range(grid_size):
        lat = center_lat + (i - grid_size // 2) * spacing
        lng = center_lng + (j - grid_size // 2) * spacing
        
        result = subprocess.run(
            ["streetview-dl", "query",
             "--lat", str(lat),
             "--lng", str(lng),
             "--radius", "50",
             "--max-results", "1",
             "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data['panoramas']:
                panoramas.append(data['panoramas'][0])

print(f"Found {len(panoramas)} unique panoramas in grid")

# Save grid results
with open('grid_panoramas.json', 'w') as f:
    json.dump(panoramas, f, indent=2)
```

### Use Cases

**Research and Analysis:**
- Create systematic coverage grids for urban analysis
- Sample panoramas along transportation routes
- Build datasets for computer vision training
- Document changes in specific areas over time

**Automation:**
- Discover panoramas programmatically without manual URL collection
- Build pipelines for large-scale Street View data extraction
- Integrate with GIS workflows and mapping applications
- Create reproducible data collection protocols

## Real-World Example: Alcatraz Island

Discovering Street View coverage on Alcatraz Island (27 acres) demonstrates both the power and limitations of coordinate-based discovery.

```bash
# Comprehensive search of small bounded area
streetview-dl query --lat 37.8267028 --lng -122.4242763 --radius 100 --max-results 150 --depth 5
```

**Results:**
- **150 panoramas discovered** in 23 seconds
- Coverage from **November 2013** and **July 2014**
- Distance range: 28m to 209m from center
- All from Google Trekker coverage of the island

**Coverage includes:**
- Main cellhouse and corridors
- Exercise yard and recreation areas
- Perimeter walkways and guard towers
- Multiple viewing angles at each location

**Example output:**
```
Found 150 panorama(s):

1. STnjKylFJk1ugwKxBWPH1w
   Date: 2013-11
   Distance: 28.1m
   Coordinates: (37.826866, -122.424033)
   Heading: 308.8°

2. CAoSFkNJSE0wb2dLRUlDQWdJQzYxb1dDREE.
   Date: 2014-07  
   Distance: 28.3m
   Coordinates: (37.826833, -122.424000)
   
... (148 more)
```

**Discovery limitations:**
Google Street View networks can have disconnected clusters. The query found 150 panoramas in the main connected network, but some isolated areas require querying their specific coordinates:

```bash
# If you know specific coordinates, query them directly
streetview-dl query --lat 37.826662 --lng -122.422901 --radius 50
# Finds 5 more in eastern cellblock area
```

**Recommended settings for small areas:**
- `--radius 100` - Good for 20-50 acre areas
- `--max-results 100-200` - Capture multiple clusters
- `--depth 5` - Deep traversal for maximum coverage
- `--max-panos 1000` - Allow thorough exploration

**Automated workflow:**
See `examples/alcatraz_example.py` for a complete Python script that:
1. Queries for Alcatraz panoramas
2. Analyzes coverage by date and distance
3. Saves results to JSON
4. Provides batch download instructions

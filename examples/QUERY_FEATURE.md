# Query Feature Summary

## Overview

The `query` command enables coordinate-based panorama discovery, unlocking automated workflows and grid-based sampling.

## Basic Usage

```bash
# Find nearest panorama
streetview-dl query --lat 34.05 --lng -118.25

# Search wider area
streetview-dl query --lat 34.05 --lng -118.25 --radius 100 --max-results 10

# JSON output for scripting
streetview-dl query --lat 34.05 --lng -118.25 --json
```

## Output Format

### Human-readable (default)

```
Found 3 panorama(s):

1. _3y4YfZwv0K7mGHOYvCB6A
   Date: 2025-10
   Distance: 5.2m
   Coordinates: (34.049958, -118.250025)

2. TVwZqqQWoyxEhc1W3cmeUg
   Date: 2025-10
   Distance: 10.0m
   Coordinates: (34.050012, -118.250108)
```

### JSON (with --json flag)

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

## Parameters

- `--lat` (required): Latitude
- `--lng` (required): Longitude
- `--radius` (default: 50): Search radius in meters
- `--max-results` (default: 5): Maximum panoramas to return
- `--json`: Output as JSON instead of human-readable
- `--verbose`: Show detailed progress
- `--api-key`: Google Maps API key (or use env var)

## Discovery Algorithm

The query command uses a multi-strategy approach to find panoramas:

1. **Progressive radius search**: Tries radius × 1, 2, 3, 5 to cast a wide net
2. **Link traversal**: Explores connected panoramas to find additional candidates
3. **Distance sorting**: Results ordered by proximity to query point
4. **Deduplication**: Each panorama appears only once in results

## Use Cases

### Grid-based Sampling

```python
# Sample 5x5 grid
for i in range(5):
    for j in range(5):
        lat = center_lat + i * 0.002
        lng = center_lng + j * 0.002
        subprocess.run([
            "streetview-dl", "query",
            "--lat", str(lat),
            "--lng", str(lng),
            "--json"
        ])
```

### Route Coverage

```python
# Query points along a route
for point in route_points:
    result = subprocess.run([
        "streetview-dl", "query",
        "--lat", str(point['lat']),
        "--lng", str(point['lng']),
        "--radius", "50",
        "--json"
    ], capture_output=True)
    # Process results...
```

### Automated Batch Download

```bash
# 1. Query area
streetview-dl query --lat 34.05 --lng -118.25 --max-results 20 --json > panos.json

# 2. Build URLs
cat panos.json | jq -r '.panoramas[] | 
  "https://www.google.com/maps/@\(.lat),\(.lng),3a,75y,0h,90t/data=!3m7!1e1!3m5!1s\(.pano_id)"' \
  > urls.txt

# 3. Download
streetview-dl --batch urls.txt --output-dir ./output/
```

## Examples

See:
- `examples/query_example.py` - Simple query → download workflow
- `examples/grid_coverage.py` - Systematic grid-based area sampling

## API Considerations

- Each query makes 1-5 API calls depending on radius and max-results
- Progressive radius search is optimized to minimize calls
- Consider rate limiting for large-scale automation
- Use `--radius` to control search area and API usage

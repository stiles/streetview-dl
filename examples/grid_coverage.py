#!/usr/bin/env python3
"""
Example: Create a grid of Street View queries and find coverage.

This demonstrates using the query command to systematically sample
an area and discover available Street View coverage.
"""

import json
import subprocess
from typing import List, Dict, Set

# Grid parameters
CENTER_LAT = 34.05
CENTER_LNG = -118.25
GRID_SIZE = 3  # 3x3 grid
SPACING = 0.002  # ~200m spacing between grid points
SEARCH_RADIUS = 100  # meters

print(f"Creating {GRID_SIZE}x{GRID_SIZE} grid centered at ({CENTER_LAT}, {CENTER_LNG})")
print(f"Grid spacing: {SPACING}° (~200m), search radius: {SEARCH_RADIUS}m\n")

panoramas_by_id: Dict[str, Dict] = {}
grid_points_checked = 0

# Query each grid point
for i in range(GRID_SIZE):
    for j in range(GRID_SIZE):
        # Calculate grid point coordinates
        lat = CENTER_LAT + (i - GRID_SIZE // 2) * SPACING
        lng = CENTER_LNG + (j - GRID_SIZE // 2) * SPACING
        
        grid_points_checked += 1
        print(f"[{grid_points_checked}/{GRID_SIZE**2}] Querying ({lat:.5f}, {lng:.5f})...", end=" ")
        
        try:
            result = subprocess.run(
                [
                    "streetview-dl", "query",
                    "--lat", str(lat),
                    "--lng", str(lng),
                    "--radius", str(SEARCH_RADIUS),
                    "--max-results", "3",
                    "--json"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            # Collect unique panoramas
            for pano in data['panoramas']:
                pano_id = pano['pano_id']
                if pano_id not in panoramas_by_id:
                    panoramas_by_id[pano_id] = pano
            
            print(f"Found {len(data['panoramas'])} pano(s)")
            
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")

# Display summary
print(f"\n{'='*60}")
print(f"Grid Coverage Summary")
print(f"{'='*60}")
print(f"Grid points checked: {grid_points_checked}")
print(f"Unique panoramas found: {len(panoramas_by_id)}")

# Group by date
by_date: Dict[str, int] = {}
for pano in panoramas_by_id.values():
    date = pano.get('date', 'unknown')
    by_date[date] = by_date.get(date, 0) + 1

print(f"\nPanoramas by capture date:")
for date in sorted(by_date.keys(), reverse=True):
    print(f"  {date}: {by_date[date]} panorama(s)")

# Save to file
output_file = "grid_coverage.json"
output_data = {
    'grid_params': {
        'center_lat': CENTER_LAT,
        'center_lng': CENTER_LNG,
        'grid_size': GRID_SIZE,
        'spacing': SPACING,
        'search_radius': SEARCH_RADIUS
    },
    'summary': {
        'points_checked': grid_points_checked,
        'unique_panoramas': len(panoramas_by_id),
        'by_date': by_date
    },
    'panoramas': list(panoramas_by_id.values())
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\nResults saved to: {output_file}")

# Generate URL list for batch download
url_file = "grid_urls.txt"
with open(url_file, 'w') as f:
    for pano in panoramas_by_id.values():
        if pano.get('lat') and pano.get('lng'):
            url = (
                f"https://www.google.com/maps/@{pano['lat']},{pano['lng']},"
                f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{pano['pano_id']}!"
            )
            f.write(url + '\n')

print(f"Generated {len(panoramas_by_id)} URLs in: {url_file}")
print("\nTo batch download all panoramas:")
print(f"  streetview-dl --batch {url_file} --output-dir ./grid_panoramas/")


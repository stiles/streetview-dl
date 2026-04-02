#!/usr/bin/env python3
"""
Example: Discovering Street View coverage on Alcatraz Island.

Alcatraz Island is a small (~27 acres / 0.012 sq mi) historic landmark
in San Francisco Bay. This example shows how to use coordinate queries
to discover available Street View panoramas on a small, bounded area.
"""

import json
import subprocess
import sys

# Alcatraz Island center coordinates
ALCATRAZ_LAT = 37.8267028
ALCATRAZ_LNG = -122.4242763

# Search parameters
# 27 acres ≈ 109,000 m² → need thorough coverage
# Using 100m radius with deep traversal and grid search for maximum discovery
SEARCH_RADIUS = 100
MAX_RESULTS = 150
SEARCH_DEPTH = 5
MAX_PANOS = 1000

print("=" * 60)
print("Alcatraz Island Street View Coverage Discovery")
print("=" * 60)
print(f"Location: ({ALCATRAZ_LAT}, {ALCATRAZ_LNG})")
print(f"Island size: ~27 acres (0.012 sq mi)")
print(f"Search radius: {SEARCH_RADIUS}m")
print(f"Max results: {MAX_RESULTS}\n")

# Query for panoramas
print("Querying Google Street View API...")
try:
    result = subprocess.run(
        [
            "streetview-dl", "query",
            "--lat", str(ALCATRAZ_LAT),
            "--lng", str(ALCATRAZ_LNG),
            "--radius", str(SEARCH_RADIUS),
            "--max-results", str(MAX_RESULTS),
            "--depth", str(SEARCH_DEPTH),
            "--max-panos", str(MAX_PANOS),
            "--json"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    
    data = json.loads(result.stdout)
    
except subprocess.CalledProcessError as e:
    print(f"Error querying panoramas: {e}")
    print(e.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    sys.exit(1)

# Analyze results
panoramas = data['panoramas']
print(f"\nDiscovered {len(panoramas)} Street View panorama(s) on Alcatraz:\n")

# Group by date
by_date = {}
for pano in panoramas:
    date = pano.get('date', 'unknown')
    if date not in by_date:
        by_date[date] = []
    by_date[date].append(pano)

# Display by capture date
for date in sorted(by_date.keys(), reverse=True):
    panos = by_date[date]
    print(f"Capture date: {date} ({len(panos)} panorama(s))")
    
    for pano in panos:
        distance = pano.get('distance_m', 'unknown')
        dist_str = f"{distance:.1f}m" if isinstance(distance, (int, float)) else distance
        coords = f"({pano['lat']:.6f}, {pano['lng']:.6f})"
        heading = f"{pano['heading']:.1f}°" if pano.get('heading') else "unknown"
        
        print(f"  • {pano['pano_id'][:22]}...")
        print(f"    Distance from center: {dist_str}")
        print(f"    Coordinates: {coords}")
        print(f"    Heading: {heading}")
    print()

# Coverage statistics
distances = [p['distance_m'] for p in panoramas if p.get('distance_m')]
if distances:
    avg_distance = sum(distances) / len(distances)
    max_distance = max(distances)
    min_distance = min(distances)
    
    print("Coverage Statistics:")
    print(f"  Nearest panorama: {min_distance:.1f}m from center")
    print(f"  Furthest panorama: {max_distance:.1f}m from center")
    print(f"  Average distance: {avg_distance:.1f}m from center")
    print()

# Save results
output_file = "alcatraz_coverage.json"
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nResults saved to: {output_file}")

# Generate URL list for batch download
url_file = "alcatraz_urls.txt"
with open(url_file, 'w') as f:
    for pano in panoramas:
        if pano.get('lat') and pano.get('lng'):
            url = (
                f"https://www.google.com/maps/@{pano['lat']},{pano['lng']},"
                f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{pano['pano_id']}!"
            )
            f.write(url + '\n')

print(f"Generated {len(panoramas)} URLs in: {url_file}")
print("\nTo batch download all panoramas:")
print(f"  streetview-dl --batch {url_file} --output-dir ./alcatraz_panoramas/")


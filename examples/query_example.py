#!/usr/bin/env python3
"""
Example: Using the query command to discover and download Street View panoramas.

This script demonstrates the workflow with JSON output:
1. Query for panoramas at a location with --json flag
2. Parse the JSON results  
3. Generate URLs and download panoramas

For simpler use cases, query without --json automatically creates a URL file!
"""

import json
import subprocess
import sys

# Example coordinates (downtown LA)
LAT = 34.05
LNG = -118.25
RADIUS = 100
MAX_RESULTS = 5

print(f"Querying Street View panoramas near ({LAT}, {LNG})...")
print(f"Search radius: {RADIUS}m, max results: {MAX_RESULTS}\n")

# Step 1: Query for panoramas with JSON output
try:
    result = subprocess.run(
        [
            "streetview-dl", "query",
            "--lat", str(LAT),
            "--lng", str(LNG),
            "--radius", str(RADIUS),
            "--max-results", str(MAX_RESULTS),
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
    print(result.stdout)
    sys.exit(1)

# Step 2: Display results
print(f"Found {data['count']} panorama(s):\n")

for i, pano in enumerate(data['panoramas'], 1):
    print(f"{i}. Pano ID: {pano['pano_id']}")
    print(f"   Date: {pano['date']}")
    print(f"   Distance: {pano['distance_m']:.1f}m")
    print(f"   Coordinates: ({pano['lat']:.6f}, {pano['lng']:.6f})")
    print()

# Step 3: Generate URLs and download
if data['panoramas']:
    # Generate URL list
    url_file = "example_urls.txt"
    with open(url_file, 'w') as f:
        for pano in data['panoramas']:
            url = (
                f"https://www.google.com/maps/@{pano['lat']},{pano['lng']},"
                f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{pano['pano_id']}!"
            )
            f.write(url + '\n')
    
    print(f"Generated {len(data['panoramas'])} URLs in: {url_file}")
    print("\nTo batch download all:")
    print(f"  streetview-dl --batch {url_file} --output-dir ./panoramas/")
    
    # Download nearest as demo
    nearest = data['panoramas'][0]
    print(f"\nDownloading nearest panorama ({nearest['pano_id'][:12]})...")
    
    url = (
        f"https://www.google.com/maps/@{nearest['lat']},{nearest['lng']},"
        f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{nearest['pano_id']}!"
    )
    
    output_filename = f"query_example_{nearest['pano_id'][:12]}.jpg"
    
    try:
        subprocess.run(
            [
                "streetview-dl",
                "--quality", "low",
                "--output", output_filename,
                url
            ],
            check=True
        )
        print(f"\nSuccess! Downloaded to: {output_filename}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error downloading panorama: {e}")
        sys.exit(1)
else:
    print("No panoramas found to download.")

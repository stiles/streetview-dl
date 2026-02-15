#!/usr/bin/env python3
"""
Generate comprehensive examples of streetview-dl CLI usage.
Creates a variety of outputs to demonstrate different options and their effects.

Usage:
    python generate_examples.py [URL] [--location LOCATION_NAME] [--output-dir DIR]

Examples:
    python generate_examples.py "https://maps.url..." --location "union_station"
    python generate_examples.py --location venice  # Uses default Venice URL
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Default Venice URL from the README
DEFAULT_URL = "https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu"

# Known locations
LOCATIONS = {
    "venice": {
        "url": DEFAULT_URL,
        "name": "venice",
        "description": "Venice, Italy - Cannaregio Canal"
    },
    "union_station": {
        "url": "https://www.google.com/maps/@34.0559932,-118.2370083,3a,60y,114.81h,95.96t/data=!3m7!1e1!3m5!1sL8uFe5HywD623RlKi4Z6-Q!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D-5.95625878629744%26panoid%3DL8uFe5HywD623RlKi4Z6-Q%26yaw%3D114.81165364156635!7i16384!8i8192?entry=ttu&g_ep=EgoyMDI2MDIxMS4wIKXMDSoASAFQAw%3D%3D",
        "name": "union_station",
        "description": "Union Station, Los Angeles"
    }
}

def run_command(cmd, description, output_dir):
    """Run a streetview-dl command and log the result."""
    print(f"\n{'='*60}")
    print(f"EXAMPLE: {description}")
    print(f"COMMAND: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("STDOUT:", result.stdout)
        else:
            print("❌ FAILED")
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    return True

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive examples of streetview-dl CLI usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_examples.py
  python generate_examples.py --location union_station
  python generate_examples.py "https://maps.url..." --location "custom_location"
  python generate_examples.py "https://maps.url..." --output-dir examples/union_station

Available preset locations: venice, union_station
        """
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="Google Maps Street View URL (defaults to Venice)"
    )
    parser.add_argument(
        "--location",
        "-l",
        help="Location name for file prefixes (e.g., 'venice', 'union_station'). Auto-detected if preset location."
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Output directory for examples (default: examples_output/<location>)"
    )
    
    return parser.parse_args()

def get_location_config(args):
    """Determine URL and location name from arguments."""
    # If URL provided, use it
    if args.url:
        url = args.url
        # Try to match against known locations
        location_name = None
        for key, config in LOCATIONS.items():
            if config["url"] == url:
                location_name = key
                break
        
        # Use provided location name or default to "location"
        if args.location:
            location_name = args.location
        elif not location_name:
            location_name = "location"
            
        description = LOCATIONS.get(location_name, {}).get("description", "Custom location")
    
    # If no URL but location specified, use preset
    elif args.location:
        if args.location in LOCATIONS:
            config = LOCATIONS[args.location]
            url = config["url"]
            location_name = config["name"]
            description = config["description"]
        else:
            print(f"❌ Unknown preset location: {args.location}")
            print(f"Available locations: {', '.join(LOCATIONS.keys())}")
            sys.exit(1)
    
    # Default to Venice
    else:
        config = LOCATIONS["venice"]
        url = config["url"]
        location_name = config["name"]
        description = config["description"]
    
    return url, location_name, description

def generate_examples(url, location_name, output_dir):
    """Generate examples for a given location."""
    
    # Basic examples
    examples = [
        # Basic quality examples
        {
            "cmd": ["streetview-dl", "--quality", "low", "--output", f"{location_name}_low_quality.jpg", url],
            "desc": "Low quality download (4K, ~1MB)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--output", f"{location_name}_medium_quality.jpg", url],
            "desc": "Medium quality download (8K, ~4MB)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "high", "--output", f"{location_name}_high_quality.jpg", url],
            "desc": "High quality download (16K, ~10MB)"
        },
        
        # Field of view examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "90", "--output", f"{location_name}_fov_90deg.jpg", url],
            "desc": "90° field of view (narrow, architectural details)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "180", "--output", f"{location_name}_fov_180deg.jpg", url],
            "desc": "180° field of view (half panorama)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "270", "--output", f"{location_name}_fov_270deg.jpg", url],
            "desc": "270° field of view (wide context)"
        },
        
        # Directional clipping examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--clip", "right", "--output", f"{location_name}_clip_forward.jpg", url],
            "desc": "Forward-facing 180° view"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--clip", "left", "--output", f"{location_name}_clip_rear.jpg", url],
            "desc": "Rear-facing 180° view"
        },
        
        # Combined FOV and clipping
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "220", "--clip", "right", "--output", f"{location_name}_fov220_clip_forward.jpg", url],
            "desc": "220° FOV with forward clipping (demonstrates clipping override)"
        },
        
        # Image filters
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "bw", "--output", f"{location_name}_blackwhite.jpg", url],
            "desc": "Black and white filter"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "sepia", "--output", f"{location_name}_sepia.jpg", url],
            "desc": "Sepia filter"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "vintage", "--output", f"{location_name}_vintage.jpg", url],
            "desc": "Vintage filter"
        },
        
        # Image adjustments
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--brightness", "1.3", "--output", f"{location_name}_bright.jpg", url],
            "desc": "Increased brightness (1.3x)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--contrast", "1.4", "--output", f"{location_name}_high_contrast.jpg", url],
            "desc": "Increased contrast (1.4x)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--saturation", "0.6", "--output", f"{location_name}_desaturated.jpg", url],
            "desc": "Reduced saturation (0.6x)"
        },
        
        # Cropping examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--crop-bottom", "0.75", "--output", f"{location_name}_crop_bottom.jpg", url],
            "desc": "Bottom crop (keep top 75% to remove ground/car)"
        },
        
        # Complex combinations
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "200", "--clip", "right", "--crop-bottom", "0.8", "--filter", "vintage", "--brightness", "1.1", "--output", f"{location_name}_complex.jpg", url],
            "desc": "Complex example: 200° FOV, forward clip, bottom crop, vintage filter, bright"
        },
        
        # Different formats
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--format", "png", "--output", f"{location_name}_format.png", url],
            "desc": "PNG format output"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--format", "webp", "--output", f"{location_name}_format.webp", url],
            "desc": "WebP format output"
        },
        
        # Size limits
        {
            "cmd": ["streetview-dl", "--quality", "high", "--max-width", "4096", "--output", f"{location_name}_max_width.jpg", url],
            "desc": "High quality with width limit (4096px max)"
        },
        
        # Metadata examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--metadata", "--output", f"{location_name}_with_metadata.jpg", url],
            "desc": "Download with metadata JSON file"
        },
        {
            "cmd": ["streetview-dl", "--metadata-only", url],
            "desc": "Extract metadata only (no image download)"
        },
    ]
    
    # Run all examples
    successful = 0
    failed = 0
    
    for example in examples:
        if run_command(example["cmd"], example["desc"], output_dir):
            successful += 1
        else:
            failed += 1
    
    return successful, failed

def main():
    """Generate comprehensive examples."""
    args = parse_args()
    
    # Get location configuration
    url, location_name, description = get_location_config(args)
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("examples_output") / location_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Generating streetview-dl examples...")
    print(f"📍 Location: {description}")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🔗 URL: {url[:80]}...")
    
    # Check if streetview-dl is available
    try:
        subprocess.run(["streetview-dl", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ streetview-dl not found. Please install it first:")
        print("   pip install -e .")
        sys.exit(1)
    
    # Generate examples
    successful, failed = generate_examples(url, location_name, output_dir)
    
    # Summary
    print(f"\n🎉 SUMMARY")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # List generated files
    output_files = list(output_dir.glob(f"{location_name}_*"))
    if output_files:
        print(f"\n📸 Generated files:")
        for file in sorted(output_files):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   {file.name} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate comprehensive examples of streetview-dl CLI usage.
Creates a variety of outputs to demonstrate different options and their effects.
"""

import os
import subprocess
import sys
from pathlib import Path

# Venice URL from the README
VENICE_URL = "https://www.google.com/maps/@45.4360629,12.3305426,3a,60y,236.1h,86.64t/data=!3m7!1e1!3m5!1sjGaYvr31o-KsarHZtXbc5w!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.357981416541378%26panoid%3DjGaYvr31o-KsarHZtXbc5w%26yaw%3D236.10458342884988!7i13312!8i6656?entry=ttu"

# Output directory
OUTPUT_DIR = Path("examples_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def run_command(cmd, description):
    """Run a streetview-dl command and log the result."""
    print(f"\n{'='*60}")
    print(f"EXAMPLE: {description}")
    print(f"COMMAND: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=OUTPUT_DIR)
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

def main():
    """Generate comprehensive examples."""
    
    print("🚀 Generating streetview-dl examples...")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print(f"🌍 Venice URL: {VENICE_URL}")
    
    # Check if streetview-dl is available
    try:
        subprocess.run(["streetview-dl", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ streetview-dl not found. Please install it first:")
        print("   pip install -e .")
        sys.exit(1)
    
    # Basic examples
    examples = [
        # Basic quality examples
        {
            "cmd": ["streetview-dl", "--quality", "low", "--output", "venice_low_quality.jpg", VENICE_URL],
            "desc": "Low quality download (4K, ~1MB)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--output", "venice_medium_quality.jpg", VENICE_URL],
            "desc": "Medium quality download (8K, ~4MB)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "high", "--output", "venice_high_quality.jpg", VENICE_URL],
            "desc": "High quality download (16K, ~10MB)"
        },
        
        # Field of view examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "90", "--output", "venice_fov_90deg.jpg", VENICE_URL],
            "desc": "90° field of view (narrow, architectural details)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "180", "--output", "venice_fov_180deg.jpg", VENICE_URL],
            "desc": "180° field of view (half panorama)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "270", "--output", "venice_fov_270deg.jpg", VENICE_URL],
            "desc": "270° field of view (wide context)"
        },
        
        # Directional clipping examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--clip", "right", "--output", "venice_clip_forward.jpg", VENICE_URL],
            "desc": "Forward-facing 180° (clip right from heading 236°)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--clip", "left", "--output", "venice_clip_rear.jpg", VENICE_URL],
            "desc": "Rear-facing 180° (clip left from heading 236°)"
        },
        
        # Combined FOV and clipping
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "220", "--clip", "right", "--output", "venice_fov220_clip_forward.jpg", VENICE_URL],
            "desc": "220° FOV with forward clipping (demonstrates clipping override)"
        },
        
        # Image filters
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "bw", "--output", "venice_blackwhite.jpg", VENICE_URL],
            "desc": "Black and white filter"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "sepia", "--output", "venice_sepia.jpg", VENICE_URL],
            "desc": "Sepia filter"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--filter", "vintage", "--output", "venice_vintage.jpg", VENICE_URL],
            "desc": "Vintage filter"
        },
        
        # Image adjustments
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--brightness", "1.3", "--output", "venice_bright.jpg", VENICE_URL],
            "desc": "Increased brightness (1.3x)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--contrast", "1.4", "--output", "venice_high_contrast.jpg", VENICE_URL],
            "desc": "Increased contrast (1.4x)"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--saturation", "0.6", "--output", "venice_desaturated.jpg", VENICE_URL],
            "desc": "Reduced saturation (0.6x)"
        },
        
        # Cropping examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--crop-bottom", "0.75", "--output", "venice_crop_bottom.jpg", VENICE_URL],
            "desc": "Bottom crop (keep top 75% to remove ground/car)"
        },
        
        # Complex combinations
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--fov", "200", "--clip", "right", "--crop-bottom", "0.8", "--filter", "vintage", "--brightness", "1.1", "--output", "venice_complex.jpg", VENICE_URL],
            "desc": "Complex example: 200° FOV, forward clip, bottom crop, vintage filter, bright"
        },
        
        # Different formats
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--format", "png", "--output", "venice_format.png", VENICE_URL],
            "desc": "PNG format output"
        },
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--format", "webp", "--output", "venice_format.webp", VENICE_URL],
            "desc": "WebP format output"
        },
        
        # Size limits
        {
            "cmd": ["streetview-dl", "--quality", "high", "--max-width", "4096", "--output", "venice_max_width.jpg", VENICE_URL],
            "desc": "High quality with width limit (4096px max)"
        },
        
        # Metadata examples
        {
            "cmd": ["streetview-dl", "--quality", "medium", "--metadata", "--output", "venice_with_metadata.jpg", VENICE_URL],
            "desc": "Download with metadata JSON file"
        },
        {
            "cmd": ["streetview-dl", "--metadata-only", VENICE_URL],
            "desc": "Extract metadata only (no image download)"
        },
    ]
    
    # Run all examples
    successful = 0
    failed = 0
    
    for example in examples:
        if run_command(example["cmd"], example["desc"]):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n🎉 SUMMARY")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    
    # List generated files
    output_files = list(OUTPUT_DIR.glob("venice_*"))
    if output_files:
        print(f"\n📸 Generated files:")
        for file in sorted(output_files):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   {file.name} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()

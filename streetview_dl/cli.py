"""Command line interface for streetview-dl."""

import json
import math
import sys
import warnings
from pathlib import Path
from typing import Optional

import click
from PIL import Image
from rich.console import Console

# Suppress PIL DecompressionBombWarning for large panorama images
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
# Also filter the specific warning message format with different patterns
warnings.filterwarnings("ignore", message=".*Image size.*exceeds limit.*")
warnings.filterwarnings("ignore", message=".*decompression bomb.*")
warnings.filterwarnings("ignore", message=".*pixels.*exceeds limit.*")
# Filter all PIL warnings for safety
warnings.filterwarnings("ignore", module="PIL.*")
# Increase PIL's decompression bomb protection limit for large panoramas
Image.MAX_IMAGE_PIXELS = None

from . import __version__
from .auth import get_api_key, configure_api_key, validate_api_key
from .core import StreetViewDownloader
from .metadata import extract_from_maps_url, validate_maps_url
from .processing import ImageProcessor
from .utils import write_xmp_metadata, crop_fov


console = Console()


@click.command()
@click.argument('url', required=False)
@click.option('--api-key', help='Google Maps API key')
@click.option('--output', '-o', help='Output filename')
@click.option('--output-dir', help='Output directory for batch processing')
@click.option('--quality', type=click.Choice(['low', 'medium', 'high']), 
              default='medium', help='Image quality/resolution')
@click.option('--format', 'output_format', type=click.Choice(['jpg', 'png', 'webp']), 
              default='jpg', help='Output image format')
@click.option('--jpeg-quality', type=click.IntRange(1, 100), default=92, 
              help='JPEG compression quality')
@click.option('--max-width', type=int, help='Maximum width (resizes if larger)')
@click.option('--fov', type=click.IntRange(60, 360), help='Field of view in degrees (crops panorama around viewing direction)')
@click.option('--filter', 'image_filter', 
              type=click.Choice(['none', 'bw', 'sepia', 'vintage']), 
              default='none', help='Apply image filter')
@click.option('--brightness', type=float, default=1.0, help='Brightness adjustment')
@click.option('--contrast', type=float, default=1.0, help='Contrast adjustment')
@click.option('--saturation', type=float, default=1.0, help='Saturation adjustment')
@click.option('--metadata', is_flag=True, help='Save metadata as JSON file')
@click.option('--metadata-only', is_flag=True, help='Extract metadata only, no download')
@click.option('--batch', help='File containing URLs (one per line)')
@click.option('--no-xmp', is_flag=True, help='Skip embedding 360° XMP metadata')
@click.option('--timeout', type=int, default=30, help='Request timeout in seconds')
@click.option('--configure', is_flag=True, help='Configure API key interactively')
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(
    url: Optional[str],
    api_key: Optional[str],
    output: Optional[str],
    output_dir: Optional[str],
    quality: str,
    output_format: str,
    jpeg_quality: int,
    max_width: Optional[int],
    fov: Optional[int],
    image_filter: str,
    brightness: float,
    contrast: float,
    saturation: float,
    metadata: bool,
    metadata_only: bool,
    batch: Optional[str],
    no_xmp: bool,
    timeout: int,
    configure: bool,
    version: bool,
    verbose: bool,
) -> None:
    """Download high-resolution Google Street View panoramas."""
    
    if version:
        click.echo(f"streetview-dl {__version__}")
        return
    
    if configure:
        configure_api_key()
        return
    
    # Handle batch processing
    if batch:
        process_batch(
            batch_file=batch,
            api_key=api_key,
            output_dir=output_dir,
            quality=quality,
            output_format=output_format,
            jpeg_quality=jpeg_quality,
            max_width=max_width,
            fov=fov,
            image_filter=image_filter,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            metadata=metadata,
            metadata_only=metadata_only,
            no_xmp=no_xmp,
            timeout=timeout,
            verbose=verbose,
        )
        return
    
    # Single URL processing
    if not url:
        click.echo("Error: URL required (or use --batch for multiple URLs)")
        click.echo("Try 'streetview-dl --help' for more information.")
        sys.exit(1)
    
    try:
        process_single_url(
            url=url,
            api_key=api_key,
            output=output,
            quality=quality,
            output_format=output_format,
            jpeg_quality=jpeg_quality,
            max_width=max_width,
            fov=fov,
            image_filter=image_filter,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            metadata=metadata,
            metadata_only=metadata_only,
            no_xmp=no_xmp,
            timeout=timeout,
            verbose=verbose,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def process_single_url(
    url: str,
    api_key: Optional[str],
    output: Optional[str],
    quality: str,
    output_format: str,
    jpeg_quality: int,
    max_width: Optional[int],
    fov: Optional[int],
    image_filter: str,
    brightness: float,
    contrast: float,
    saturation: float,
    metadata: bool,
    metadata_only: bool,
    no_xmp: bool,
    timeout: int,
    verbose: bool,
) -> None:
    """Process a single URL."""
    
    # Validate URL
    if not validate_maps_url(url):
        raise click.ClickException("Invalid Google Maps Street View URL")
    
    # Get API key
    try:
        api_key = get_api_key(api_key)
        if not validate_api_key(api_key):
            raise click.ClickException("Invalid API key format")
    except Exception as e:
        raise click.ClickException(f"API key error: {e}")
    
    # Initialize downloader
    downloader = StreetViewDownloader(api_key=api_key, timeout=timeout)
    
    # Extract panorama info
    pano_id, yaw, pitch = extract_from_maps_url(url)
    if not pano_id:
        raise click.ClickException("Could not extract panorama ID from URL")
    
    if verbose:
        console.print(f"[dim]Panorama ID: {pano_id}[/dim]")
        if yaw is not None:
            console.print(f"[dim]Yaw: {yaw:.2f}°[/dim]")
        if pitch is not None:
            console.print(f"[dim]Pitch: {pitch:.2f}°[/dim]")
    
    # Get metadata
    with console.status("[bold blue]Fetching metadata..."):
        street_view_metadata = downloader.get_metadata(pano_id=pano_id)
        street_view_metadata.url_yaw = yaw
        street_view_metadata.url_pitch = pitch
    
    if verbose:
        console.print(f"[dim]Resolution: {street_view_metadata.image_width}×{street_view_metadata.image_height}[/dim]")
        if street_view_metadata.date:
            console.print(f"[dim]Date: {street_view_metadata.date}[/dim]")
    
    # Generate output filename if not provided
    if not output:
        quality_suffix = f"_{quality}" if quality != "medium" else ""
        fov_suffix = f"_{fov}deg" if fov and fov < 360 else ""
        filter_suffix = f"_{image_filter}" if image_filter != "none" else ""
        output = f"streetview_{pano_id}{quality_suffix}{fov_suffix}{filter_suffix}.{output_format}"
    
    # Save metadata if requested
    if metadata or metadata_only:
        metadata_file = Path(output).with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(street_view_metadata.to_dict(), f, indent=2)
        console.print(f"[green]Metadata saved: {metadata_file}[/green]")
    
    if metadata_only:
        return
    
    # Calculate total tiles for progress (match core module calculation)
    zoom_map = {"low": 3, "medium": 4, "high": 5}
    z = zoom_map.get(quality, 5)
    scale_factor = 2 ** (5 - z)
    scaled_width = street_view_metadata.image_width // scale_factor
    scaled_height = street_view_metadata.image_height // scale_factor
    tiles_x = math.ceil(scaled_width / street_view_metadata.tile_width)
    tiles_y = math.ceil(scaled_height / street_view_metadata.tile_height)
    total_tiles = tiles_x * tiles_y
    
    # Download panorama with status updates
    console.print("[blue]Fetching panorama tiles...[/blue]")
    image = downloader.download_panorama(
        street_view_metadata, 
        quality=quality,
        console=console
    )
    
    # Process image
    console.print("[blue]Processing image...[/blue]")
    processor = ImageProcessor()
    
    # Apply field-of-view cropping if specified
    if fov and fov < 360 and street_view_metadata.url_yaw is not None:
        console.print(f"[blue]Cropping to {fov}° field of view...[/blue]")
        image = crop_fov(image, street_view_metadata.url_yaw, fov)
        if verbose:
            console.print(f"[dim]Cropped to {fov}° around yaw {street_view_metadata.url_yaw:.1f}°[/dim]")
    
    if max_width and image.width > max_width:
        scale = max_width / image.width
        new_height = int(image.height * scale)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        if verbose:
            console.print(f"[dim]Resized to: {max_width}×{new_height}[/dim]")
    
    if image_filter != "none" or brightness != 1.0 or contrast != 1.0 or saturation != 1.0:
        console.print("[blue]Applying filters and adjustments...[/blue]")
        image = processor.apply_filter(image, image_filter)
        image = processor.adjust_image(image, brightness, contrast, saturation)
    
    # Save image
    console.print("[blue]Saving panorama...[/blue]")
    save_kwargs = {}
    format_for_save = output_format.upper()
    if format_for_save == 'JPG':
        format_for_save = 'JPEG'
        save_kwargs['quality'] = jpeg_quality
        save_kwargs['optimize'] = True
    
    # Save with warning suppression for large images
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
        image.save(output, format=format_for_save, **save_kwargs)
    
    # Add XMP metadata for 360° photos
    if not no_xmp and output_format.lower() == 'jpg':
        console.print("[blue]Adding 360° metadata...[/blue]")
        write_xmp_metadata(output, image)
    
    # Display results
    file_size = Path(output).stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    console.print(f"[green]✓ Saved: {output}[/green]")
    console.print(f"[dim]Size: {file_size_mb:.1f} MB[/dim]")
    
    if street_view_metadata.copyright_info:
        console.print(f"[dim]Copyright: {street_view_metadata.copyright_info}[/dim]")


def process_batch(
    batch_file: str,
    api_key: Optional[str],
    output_dir: Optional[str],
    quality: str,
    output_format: str,
    jpeg_quality: int,
    max_width: Optional[int],
    fov: Optional[int],
    image_filter: str,
    brightness: float,
    contrast: float,
    saturation: float,
    metadata: bool,
    metadata_only: bool,
    no_xmp: bool,
    timeout: int,
    verbose: bool,
) -> None:
    """Process multiple URLs from a batch file."""
    
    # Read URLs
    try:
        with open(batch_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except IOError as e:
        raise click.ClickException(f"Could not read batch file: {e}")
    
    if not urls:
        raise click.ClickException("No URLs found in batch file")
    
    # Setup output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()
    
    console.print(f"[blue]Processing {len(urls)} URLs...[/blue]")
    
    success_count = 0
    error_count = 0
    
    for i, url in enumerate(urls, 1):
        console.print(f"\n[bold]({i}/{len(urls)})[/bold] Processing: {url[:80]}...")
        
        try:
            # Generate output filename
            pano_id, _, _ = extract_from_maps_url(url)
            if pano_id:
                quality_suffix = f"_{quality}" if quality != "medium" else ""
                fov_suffix = f"_{fov}deg" if fov and fov < 360 else ""
                filter_suffix = f"_{image_filter}" if image_filter != "none" else ""
                filename = f"streetview_{pano_id}{quality_suffix}{fov_suffix}{filter_suffix}.{output_format}"
                output = str(output_path / filename)
            else:
                output = str(output_path / f"streetview_{i:03d}.{output_format}")
            
            process_single_url(
                url=url,
                api_key=api_key,
                output=output,
                quality=quality,
                output_format=output_format,
                jpeg_quality=jpeg_quality,
                max_width=max_width,
                fov=fov,
                image_filter=image_filter,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                metadata=metadata,
                metadata_only=metadata_only,
                no_xmp=no_xmp,
                timeout=timeout,
                verbose=verbose,
            )
            success_count += 1
            
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            error_count += 1
            if verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    # Summary
    console.print(f"\n[bold]Batch complete:[/bold]")
    console.print(f"[green]✓ Successful: {success_count}[/green]")
    if error_count:
        console.print(f"[red]✗ Failed: {error_count}[/red]")


if __name__ == "__main__":
    main()

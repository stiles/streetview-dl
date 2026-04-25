"""Command line interface for streetview-dl."""

import json
import time
import sys
import os
import warnings
from pathlib import Path
from typing import Optional

import click
from PIL import Image
from rich.console import Console

from . import __version__
from .auth import get_api_key, configure_api_key, validate_api_key
from .core import StreetViewDownloader
from .metadata import extract_from_maps_url, validate_maps_url
from .processing import ImageProcessor
from .utils import write_xmp_metadata, crop_fov, crop_bottom_fraction, crop_horizontal_section

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


console = Console()


def resolve_accent(color: str) -> str:
    """Map a simple color name to a bright accent used in Rich markup."""
    if color == "yellow":
        return "bright_yellow"
    return "bright_cyan"


def determine_concurrency(quality: str, requested: int) -> int:
    """Auto-tune concurrency when requested == 0; otherwise return requested.

    Uses CPU count and quality to pick a conservative parallelism that balances
    speed with API etiquette. Users can override via flag or env var.
    """
    if requested and requested > 0:
        return requested

    env = os.getenv("STREETVIEW_DL_CONCURRENCY")
    if env:
        try:
            val = int(env)
            if 1 <= val <= 32:
                return val
        except ValueError:
            pass

    cpu = os.cpu_count() or 4
    if quality == "high":
        base = min(16, max(4, cpu * 2))
    elif quality == "medium":
        base = min(12, max(3, cpu))
    else:
        base = min(8, max(2, max(1, cpu // 2)))
    return max(1, min(32, base))


@click.command()
@click.argument("url", required=False)
@click.option("--api-key", help="Google Maps API key")
@click.option("--output", "-o", help="Output filename")
@click.option("--output-dir", help="Output directory for batch processing")
@click.option(
    "--quality",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Image quality/resolution",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["jpg", "png", "webp"]),
    default="jpg",
    help="Output image format",
)
@click.option(
    "--jpeg-quality",
    type=click.IntRange(1, 100),
    default=92,
    help="JPEG compression quality",
)
@click.option(
    "--max-width", type=int, help="Maximum width (resizes if larger)"
)
@click.option(
    "--fov",
    type=click.IntRange(60, 360),
    help="Field of view in degrees (crops panorama around viewing direction)",
)
@click.option(
    "--filter",
    "image_filter",
    type=click.Choice(["none", "bw", "sepia", "vintage"]),
    default="none",
    help="Apply image filter",
)
@click.option(
    "--brightness", type=float, default=1.0, help="Brightness adjustment"
)
@click.option(
    "--contrast", type=float, default=1.0, help="Contrast adjustment"
)
@click.option(
    "--saturation", type=float, default=1.0, help="Saturation adjustment"
)
@click.option(
    "--clip",
    type=click.Choice(["none", "left", "right"]),
    default="none",
    help="Clip to half panorama relative to view direction",
)
@click.option(
    "--crop-bottom",
    type=float,
    default=0.75,
    help="Keep top fraction of height (0.0-1.0), e.g. 0.75",
)
@click.option(
    "--no-crop",
    is_flag=True,
    help="Disable default bottom cropping (keep full image height)",
)
@click.option("--metadata", is_flag=True, help="Save metadata as JSON file")
@click.option(
    "--metadata-only", is_flag=True, help="Extract metadata only, no download"
)
@click.option(
    "--historical", is_flag=True, help="Discover and list historical imagery dates for this location"
)
@click.option(
    "--historical-download", is_flag=True, help="Download all available historical images for this location"
)
@click.option(
    "--historical-max-depth",
    type=click.IntRange(1, 10),
    default=7,
    help="Maximum link traversal depth for historical discovery (1-10, default: 7)",
)
@click.option(
    "--historical-max-panoramas",
    type=click.IntRange(50, 500),
    default=200,
    help="Maximum panoramas to check during historical discovery (50-500, default: 200)",
)
@click.option("--batch", help="File containing URLs (one per line)")
@click.option(
    "--no-xmp", is_flag=True, help="Skip embedding 360° XMP metadata"
)
@click.option(
    "--timeout", type=int, default=30, help="Request timeout in seconds"
)
@click.option(
    "--retries",
    type=click.IntRange(0, 10),
    default=3,
    envvar="STREETVIEW_DL_RETRIES",
    show_envvar=True,
    help="HTTP retry attempts",
)
@click.option(
    "--backoff", type=float, default=0.5, help="Retry backoff factor (seconds)"
)
@click.option("--lat", type=float, help="Latitude (use with --lng for coordinate download)")
@click.option("--lng", type=float, help="Longitude (use with --lat for coordinate download)")
@click.option("--quick", "-q", help="Quick download by coordinates 'lat,lng' (e.g. 42.5,-94.1)")
@click.option("--radius", type=int, default=50, help="Search radius in meters (default: 50)")
@click.option(
    "--configure", is_flag=True, help="Configure API key interactively"
)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--accent-color",
    type=click.Choice(["cyan", "yellow"]),
    default="cyan",
    help="Accent color for status text",
)
@click.option(
    "--concurrency",
    type=click.IntRange(0, 32),
    default=0,
    envvar="STREETVIEW_DL_CONCURRENCY",
    show_envvar=True,
    help="Parallel tile download workers (0=auto)",
)
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
    clip: str,
    crop_bottom: float,
    no_crop: bool,
    metadata: bool,
    metadata_only: bool,
    historical: bool,
    historical_download: bool,
    historical_max_depth: int,
    historical_max_panoramas: int,
    batch: Optional[str],
    no_xmp: bool,
    timeout: int,
    retries: int,
    backoff: float,
    configure: bool,
    version: bool,
    verbose: bool,
    accent_color: str,
    concurrency: int,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    quick: Optional[str] = None,
    radius: int = 50,
) -> None:
    """Download high-resolution Google Street View panoramas."""

    if version:
        click.echo(f"streetview-dl {__version__}")
        return

    if configure:
        configure_api_key()
        return

    # Handle --no-crop flag
    if no_crop:
        crop_bottom = 1.0

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
            clip=clip,
            crop_bottom=crop_bottom,
            metadata=metadata,
            metadata_only=metadata_only,
            no_xmp=no_xmp,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
            verbose=verbose,
            accent_color=accent_color,
            concurrency=concurrency,
        )
        return

    # Handle --quick option (parses lat,lng string)
    if quick:
        try:
            if "," not in quick:
                raise click.ClickException("Invalid --quick format. Use 'lat,lng' (e.g., --quick 42.5,-94.1)")
            q_lat, q_lng = map(str.strip, quick.split(","))
            lat = float(q_lat)
            lng = float(q_lng)
        except ValueError:
            raise click.ClickException("Invalid coordinates in --quick. Must be numeric 'lat,lng'")

    # Single URL or coordinate processing
    if not url and (lat is None or lng is None):
        click.echo("Error: URL required (or use --quick 'lat,lng', or --batch for multiple URLs)")
        click.echo("\nTo DISCOVER multiple panoramas in an area, use the 'query' command:")
        click.echo("  streetview-dl query --lat 42.5 --lng -94.1")
        click.echo("\nTo QUICKLY download the nearest panorama, use --quick:")
        click.echo("  streetview-dl --quick 42.5,-94.1")
        sys.exit(1)

    try:
        process_location(
            url=url,
            lat=lat,
            lng=lng,
            radius=radius,
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
            clip=clip,
            crop_bottom=crop_bottom,
            no_crop=no_crop,
            metadata=metadata,
            metadata_only=metadata_only,
            historical=historical,
            historical_download=historical_download,
            historical_max_depth=historical_max_depth,
            historical_max_panoramas=historical_max_panoramas,
            no_xmp=no_xmp,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
            verbose=verbose,
            accent_color=accent_color,
            concurrency=concurrency,
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


def process_location(
    url: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    radius: int,
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
    clip: str,
    crop_bottom: float,
    no_crop: bool,
    metadata: bool,
    metadata_only: bool,
    historical: bool,
    historical_download: bool,
    historical_max_depth: int,
    historical_max_panoramas: int,
    no_xmp: bool,
    timeout: int,
    retries: int,
    backoff: float,
    verbose: bool,
    accent_color: str,
    concurrency: int,
) -> None:
    """Process a panorama by URL or coordinates."""
    accent = resolve_accent(accent_color)
    start_time = time.perf_counter()

    # Handle --no-crop flag
    if no_crop:
        crop_bottom = 1.0
    
    # Extract panorama info
    if url:
        # Validate URL
        if not validate_maps_url(url):
            raise click.ClickException("Invalid Google Maps Street View URL")
        pano_id, yaw, pitch, url_fov, mode_token, url_date = extract_from_maps_url(url)
        if not pano_id:
            raise click.ClickException("Could not extract panorama ID from URL")
    else:
        # Coordinates will be used in get_metadata below
        pano_id = None
        yaw = None
        pitch = None
        url_fov = None
        mode_token = None
        url_date = None

    # Get API key
    try:
        api_key = get_api_key(api_key)
        if not validate_api_key(api_key):
            raise click.ClickException("Invalid API key format")
    except Exception as e:
        raise click.ClickException(f"API key error: {e}")

    # Initialize downloader
    downloader = StreetViewDownloader(
        api_key=api_key, timeout=timeout, retries=retries, backoff=backoff
    )

    # Get metadata
    with console.status(f"[bold {accent}]Fetching metadata..."):
        if pano_id:
            street_view_metadata = downloader.get_metadata(pano_id=pano_id)
        else:
            street_view_metadata = downloader.get_metadata(lat=lat, lng=lng, radius=radius)
            pano_id = street_view_metadata.pano_id
            
        street_view_metadata.url_yaw = yaw
        street_view_metadata.url_pitch = pitch
        street_view_metadata.url_fov = url_fov  # Use URL-extracted FOV, not CLI FOV
        street_view_metadata.url_mode_token = mode_token
        street_view_metadata.url_date = url_date

    # Validate option combinations
    if clip in ("left", "right") and fov and fov < 180:
        console.print(
            f"[yellow]Warning: Using --clip {clip} with --fov {fov}° may produce unexpected results. "
            f"Consider using --fov 180 or larger, or omit --fov to let --clip determine the field of view.[/yellow]"
        )

    if verbose:
        console.print(f"[dim]Panorama ID: {pano_id}[/dim]")
        if yaw is not None:
            console.print(f"[dim]Yaw: {yaw:.2f}°[/dim]")
        if pitch is not None:
            console.print(f"[dim]Pitch: {pitch:.2f}°[/dim]")
        console.print(
            f"[dim]Resolution: {street_view_metadata.image_width}×{street_view_metadata.image_height}[/dim]"
        )
        if street_view_metadata.date:
            console.print(f"[dim]Date: {street_view_metadata.date}[/dim]")
        if url_date:
            console.print(f"[dim]URL Date: {url_date}[/dim]")

    # Handle historical discovery mode
    if historical or historical_download:
        if not street_view_metadata.lat or not street_view_metadata.lng:
            raise click.ClickException("Cannot discover historical imagery: no coordinates available")
        
        console.print(f"[{accent}]Discovering historical imagery...[/{accent}]")
        if verbose:
            console.print(f"[dim]Using max_depth={historical_max_depth}, max_panoramas={historical_max_panoramas}[/dim]")
        historical_panoramas = downloader.discover_historical_dates(
            lat=street_view_metadata.lat,
            lng=street_view_metadata.lng,
            max_depth=historical_max_depth,
            max_panoramas=historical_max_panoramas,
            console=console
        )
        
        if not historical_panoramas:
            console.print("[yellow]No historical imagery found for this location[/yellow]")
            return
        
        # Display historical dates
        console.print(f"\n[bold]Found {len(historical_panoramas)} panorama(s):[/bold]")
        for i, pano in enumerate(historical_panoramas, 1):
            current_marker = " [green](current)[/green]" if pano.get('is_current') else ""
            console.print(f"  {i}. {pano['date']} - {pano['pano_id']}{current_marker}")
        
        if historical and not historical_download:
            # Just list, don't download
            return
        
        # Download all historical images
        console.print(f"\n[{accent}]Downloading {len(historical_panoramas)} historical panorama(s)...[/{accent}]")
        for i, pano in enumerate(historical_panoramas, 1):
            try:
                console.print(f"\n[bold]({i}/{len(historical_panoramas)})[/bold] Downloading {pano['date']} panorama...")
                
                # Get metadata for this specific panorama
                pano_metadata = downloader.get_metadata(pano_id=pano['pano_id'])
                
                # Generate filename with date
                date_suffix = f"_{pano['date']}" if pano['date'] else ""
                quality_suffix = f"_{quality}" if quality != "medium" else ""
                fov_suffix = f"_{fov}deg" if fov and fov < 360 else ""
                filter_suffix = f"_{image_filter}" if image_filter != "none" else ""
                historical_output = f"streetview_{pano['pano_id']}{date_suffix}{quality_suffix}{fov_suffix}{filter_suffix}.{output_format}"
                
                # Download and process the panorama
                tuned_concurrency = determine_concurrency(quality, concurrency)
                image = downloader.download_panorama(
                    pano_metadata, quality, console, tuned_concurrency
                )
                
                # Process image
                processor = ImageProcessor()
                
                # Apply horizontal cropping if specified
                if (
                    (fov and fov < 360) or clip in ("left", "right")
                ) and pano_metadata.url_yaw is not None:
                    effective_fov = fov if fov else 360
                    image = crop_horizontal_section(
                        image, pano_metadata.url_yaw, effective_fov, clip
                    )
                
                # Apply filters and adjustments
                image = processor.apply_filter(image, image_filter)
                image = processor.adjust_image(image, brightness, contrast, saturation)
                
                # Apply vertical cropping
                if crop_bottom < 1.0:
                    image = crop_bottom_fraction(image, crop_bottom)
                
                # Resize if needed
                if max_width and image.width > max_width:
                    image = processor.resize_if_larger(image, max_width)
                
                # Save image
                save_kwargs = {}
                if output_format.lower() == "jpg":
                    save_kwargs["format"] = "JPEG"
                    save_kwargs["quality"] = jpeg_quality
                    save_kwargs["optimize"] = True
                else:
                    save_kwargs["format"] = output_format.upper()
                
                image.save(historical_output, **save_kwargs)
                
                # Add XMP metadata for 360° viewers
                if not no_xmp and output_format.lower() == "jpg":
                    write_xmp_metadata(historical_output, image)
                
                # Save metadata if requested
                if metadata:
                    metadata_file = Path(historical_output).with_suffix(".json")
                    with open(metadata_file, "w") as f:
                        json.dump(pano_metadata.to_dict(), f, indent=2)
                
                console.print(f"[green]✓[/green] Saved: {historical_output}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to download {pano['date']}: {e}")
                continue
        
        elapsed = time.perf_counter() - start_time
        console.print(f"\n[{accent}]Historical download completed in {elapsed:.1f}s[/{accent}]")
        return

    # Generate output filename if not provided
    if not output:
        quality_suffix = f"_{quality}" if quality != "medium" else ""
        fov_suffix = f"_{fov}deg" if fov and fov < 360 else ""
        filter_suffix = f"_{image_filter}" if image_filter != "none" else ""
        output = f"streetview_{pano_id}{quality_suffix}{fov_suffix}{filter_suffix}.{output_format}"

    # Save metadata if requested
    if metadata or metadata_only:
        metadata_file = Path(output).with_suffix(".json")
        with open(metadata_file, "w") as f:
            json.dump(street_view_metadata.to_dict(), f, indent=2)
        console.print(f"[green]Metadata saved: {metadata_file}[/green]")

    if metadata_only:
        return

    # Note: Core downloader handles tile calculations internally

    # Download panorama with status updates
    with console.status(f"[bold {accent}]Fetching panorama tiles..."):
        tuned_concurrency = determine_concurrency(quality, concurrency)
        image = downloader.download_panorama(
            street_view_metadata,
            quality=quality,
            console=console,
            concurrency=tuned_concurrency,
        )

    # Process image
    with console.status(f"[bold {accent}]Processing image..."):
        processor = ImageProcessor()

        # Apply horizontal cropping (FOV and/or directional clipping) if specified
        if (
            (fov and fov < 360) or clip in ("left", "right")
        ) and street_view_metadata.url_yaw is not None:
            # Use unified cropping function that handles both FOV and clipping
            effective_fov = fov if fov else 360
            image = crop_horizontal_section(
                image, street_view_metadata.url_yaw, effective_fov, clip
            )
            
            if verbose:
                if clip in ("left", "right"):
                    direction_text = "forward" if clip == "right" else "rear"
                    if fov and fov < 360:
                        console.print(
                            f"[dim]Cropped to {fov}° {direction_text} half around yaw {street_view_metadata.url_yaw:.1f}°[/dim]"
                        )
                    else:
                        console.print(
                            f"[dim]Clipped to {direction_text} 180° half around yaw {street_view_metadata.url_yaw:.1f}°[/dim]"
                        )
                else:
                    console.print(
                        f"[dim]Cropped to {fov}° around yaw {street_view_metadata.url_yaw:.1f}°[/dim]"
                    )

        if max_width and image.width > max_width:
            scale = max_width / image.width
            new_height = int(image.height * scale)
            image = image.resize(
                (max_width, new_height), Image.Resampling.LANCZOS
            )
            if verbose:
                console.print(
                    f"[dim]Resized to: {max_width}×{new_height}[/dim]"
                )

        if (
            image_filter != "none"
            or brightness != 1.0
            or contrast != 1.0
            or saturation != 1.0
        ):
            image = processor.apply_filter(image, image_filter)
            image = processor.adjust_image(
                image, brightness, contrast, saturation
            )

        # Bottom crop if requested (< 1.0 keeps top fraction)
        if 0.0 <= crop_bottom < 1.0:
            image = crop_bottom_fraction(image, crop_bottom)
            if verbose:
                console.print(
                    f"[dim]Cropped bottom to {int(crop_bottom*100)}% height[/dim]"
                )

    # Save image
    with console.status(f"[bold {accent}]Saving panorama..."):
        save_kwargs = {}
        format_for_save = output_format.upper()
        if format_for_save == "JPG":
            format_for_save = "JPEG"
            save_kwargs["quality"] = jpeg_quality
            save_kwargs["optimize"] = True

        # Save with warning suppression for large images
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=Image.DecompressionBombWarning
            )
            image.save(output, format=format_for_save, **save_kwargs)

    # Add XMP metadata for 360° photos
    if not no_xmp and output_format.lower() == "jpg":
        with console.status(f"[bold {accent}]Adding 360° metadata..."):
            write_xmp_metadata(output, image)

    # Display results
    file_size = Path(output).stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    console.print(f"[green]✓ Saved: {output}[/green]")
    console.print(f"[dim]Size: {file_size_mb:.1f} MB[/dim]")
    # Summary block
    elapsed = time.perf_counter() - start_time
    dims = f"{image.width}×{image.height}"
    adjustments = []
    if brightness != 1.0:
        adjustments.append(f"brightness={brightness:.2f}")
    if contrast != 1.0:
        adjustments.append(f"contrast={contrast:.2f}")
    if saturation != 1.0:
        adjustments.append(f"saturation={saturation:.2f}")
    adjustments_str = ", ".join(adjustments) if adjustments else "none"
    fov_str = f"{fov}°" if fov and fov < 360 else "360°"
    console.print(f"[bold {accent}]Summary[/bold {accent}]")
    console.print(
        f"[dim]Elapsed:[/dim] {elapsed:.2f}s  [dim]Dimensions:[/dim] {dims}  [dim]Quality:[/dim] {quality}"
    )
    console.print(
        f"[dim]FOV:[/dim] {fov_str}  [dim]Filter:[/dim] {image_filter}  [dim]Adjustments:[/dim] {adjustments_str}"
    )

    if street_view_metadata.copyright_info:
        console.print(
            f"[dim]Copyright: {street_view_metadata.copyright_info}[/dim]"
        )


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
    clip: str,
    crop_bottom: float,
    metadata: bool,
    metadata_only: bool,
    no_xmp: bool,
    timeout: int,
    retries: int,
    backoff: float,
    verbose: bool,
    accent_color: str,
    concurrency: int,
) -> None:
    """Process multiple URLs from a batch file."""
    accent = resolve_accent(accent_color)

    # Read URLs
    try:
        with open(batch_file, "r") as f:
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

    console.print(f"[{accent}]Processing {len(urls)} URLs...[/{accent}]")

    success_count = 0
    error_count = 0

    for i, url in enumerate(urls, 1):
        console.print(
            f"\n[bold]({i}/{len(urls)})[/bold] Processing: {url[:80]}..."
        )

        try:
            # Generate output filename
            pano_id, _, _, _, _, _ = extract_from_maps_url(url)
            if pano_id:
                quality_suffix = f"_{quality}" if quality != "medium" else ""
                fov_suffix = f"_{fov}deg" if fov and fov < 360 else ""
                filter_suffix = (
                    f"_{image_filter}" if image_filter != "none" else ""
                )
                filename = f"streetview_{pano_id}{quality_suffix}{fov_suffix}{filter_suffix}.{output_format}"
                output = str(output_path / filename)
            else:
                output = str(
                    output_path / f"streetview_{i:03d}.{output_format}"
                )

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
                clip=clip,
                crop_bottom=crop_bottom,
                no_crop=False,  # already processed in main()
                metadata=metadata,
                metadata_only=metadata_only,
                historical=False,
                historical_download=False,
                historical_max_depth=7,
                historical_max_panoramas=200,
                no_xmp=no_xmp,
                timeout=timeout,
                retries=retries,
                backoff=backoff,
                verbose=verbose,
                accent_color=accent_color,
                concurrency=concurrency,
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


@click.command()
@click.option("--lat", type=float, required=True, help="Latitude")
@click.option("--lng", type=float, required=True, help="Longitude")
@click.option("--radius", type=int, default=50, help="Search radius in meters (default: 50)")
@click.option("--max-results", type=int, default=5, help="Maximum number of panoramas to return (default: 5)")
@click.option("--depth", type=click.IntRange(1, 5), default=None, help="Link traversal depth (1-5, auto if not set)")
@click.option("--max-panos", type=int, default=200, help="Maximum panoramas to check during discovery (default: 200)")
@click.option("--api-key", help="Google Maps API key")
@click.option(
    "--timeout", type=int, default=30, help="Request timeout in seconds"
)
@click.option(
    "--retries",
    type=click.IntRange(0, 10),
    default=3,
    envvar="STREETVIEW_DL_RETRIES",
    show_envvar=True,
    help="HTTP retry attempts",
)
@click.option(
    "--backoff", type=float, default=0.5, help="Retry backoff factor (seconds)"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--accent-color",
    type=click.Choice(["cyan", "yellow"]),
    default="cyan",
    help="Accent color for status text",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def query_command(
    lat: float,
    lng: float,
    radius: int,
    max_results: int,
    depth: Optional[int],
    max_panos: int,
    api_key: Optional[str],
    timeout: int,
    retries: int,
    backoff: float,
    verbose: bool,
    accent_color: str,
    output_json: bool,
) -> None:
    """Query Street View panoramas by coordinates.
    
    Discover nearby panoramas at a given location. Returns pano_id, 
    date, coordinates, and distance for each candidate.
    
    Examples:
    
        # Find nearest panorama
        streetview-dl query --lat 34.05 --lng -118.25
        
        # Search wider area with multiple results
        streetview-dl query --lat 34.05 --lng -118.25 --radius 100 --max-results 10
        
        # JSON output for automation
        streetview-dl query --lat 34.05 --lng -118.25 --json
    """
    import json
    from math import radians, sin, cos, sqrt, atan2
    from collections import deque
    
    accent = resolve_accent(accent_color)
    
    # Get API key
    try:
        api_key = get_api_key(api_key)
        if not validate_api_key(api_key):
            raise click.ClickException("Invalid API key format")
    except Exception as e:
        raise click.ClickException(f"API key error: {e}")
    
    # Initialize downloader
    downloader = StreetViewDownloader(
        api_key=api_key, timeout=timeout, retries=retries, backoff=backoff
    )
    
    if not output_json:
        console.print(f"[{accent}]Searching for panoramas near ({lat}, {lng})...[/{accent}]")
        if verbose:
            console.print(f"[dim]Search radius: {radius}m, max results: {max_results}[/dim]")
    
    # Helper function to calculate distance between two lat/lng points
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in meters between two lat/lng points."""
        R = 6371000  # Earth radius in meters
        
        lat1_rad, lng1_rad = radians(lat1), radians(lng1)
        lat2_rad, lng2_rad = radians(lat2), radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    # Discover panoramas using breadth-first search with link traversal
    panoramas_by_id = {}
    checked_panos = set()
    
    # Queue for BFS: (pano_id, depth)
    from collections import deque
    to_check = deque()
    
    # Maximum depth to traverse (deeper = more panoramas but more API calls)
    # Auto-tune based on max_results if not specified
    if depth is None:
        if max_results <= 5:
            max_depth = 2
        elif max_results <= 20:
            max_depth = 3
        else:
            max_depth = 4
    else:
        max_depth = depth
    
    try:
        # Strategy 1: Multiple radius searches at center point
        search_radii = [radius]
        if max_results > 1:
            search_radii.extend([radius * 2, radius * 3, radius * 5])
        
        if not output_json and verbose:
            console.print(f"[dim]Trying search radii: {search_radii}[/dim]")
        
        for search_radius in search_radii:
            try:
                metadata = downloader.get_metadata(lat=lat, lng=lng, radius=search_radius)
                
                if metadata.pano_id not in checked_panos:
                    checked_panos.add(metadata.pano_id)
                    
                    # Calculate distance from query point
                    if metadata.lat and metadata.lng:
                        distance = haversine_distance(lat, lng, metadata.lat, metadata.lng)
                    else:
                        distance = None
                    
                    panoramas_by_id[metadata.pano_id] = {
                        'pano_id': metadata.pano_id,
                        'date': metadata.date,
                        'lat': metadata.lat,
                        'lng': metadata.lng,
                        'distance_m': round(distance, 1) if distance else None,
                        'heading': metadata.heading,
                        'copyright': metadata.copyright_info,
                    }
                    
                    # Add to BFS queue for link traversal
                    to_check.append((metadata.pano_id, 0))
                    
                    if verbose and not output_json:
                        console.print(f"  Found seed pano: {metadata.pano_id} at {search_radius}m radius")
                
            except Exception as e:
                if verbose and not output_json:
                    console.print(f"[yellow]Warning: Search at radius {search_radius}m failed: {e}[/yellow]")
                continue
        
        # Strategy 2: Grid-based searches to find disconnected clusters
        # This helps discover separate pano networks that aren't linked
        if max_results > 10:
            import math
            
            # Create a grid of search points within the search area
            grid_spacing = radius / 2  # Half the radius for overlap
            grid_points = []
            
            # Calculate number of grid cells needed
            cells = 3 if max_results < 50 else 5  # 3x3 or 5x5 grid
            
            for i in range(-cells // 2, cells // 2 + 1):
                for j in range(-cells // 2, cells // 2 + 1):
                    if i == 0 and j == 0:
                        continue  # Skip center, already searched
                    
                    # Convert meters to degrees (approximate)
                    lat_offset = (i * grid_spacing) / 111000  # ~111km per degree latitude
                    lng_offset = (j * grid_spacing) / (111000 * math.cos(math.radians(lat)))  # Adjust for latitude
                    
                    grid_points.append((lat + lat_offset, lng + lng_offset))
            
            if not output_json and verbose:
                console.print(f"[dim]Searching {len(grid_points)} grid points...[/dim]")
            
            for grid_lat, grid_lng in grid_points:
                if len(checked_panos) >= max_panos:
                    break
                
                try:
                    metadata = downloader.get_metadata(lat=grid_lat, lng=grid_lng, radius=radius // 2)
                    
                    if metadata.pano_id not in checked_panos:
                        checked_panos.add(metadata.pano_id)
                        
                        if metadata.lat and metadata.lng:
                            distance = haversine_distance(lat, lng, metadata.lat, metadata.lng)
                        else:
                            distance = None
                        
                        panoramas_by_id[metadata.pano_id] = {
                            'pano_id': metadata.pano_id,
                            'date': metadata.date,
                            'lat': metadata.lat,
                            'lng': metadata.lng,
                            'distance_m': round(distance, 1) if distance else None,
                            'heading': metadata.heading,
                            'copyright': metadata.copyright_info,
                        }
                        
                        # Add to BFS queue
                        to_check.append((metadata.pano_id, 0))
                        
                        if verbose and not output_json:
                            dist_str = f"{distance:.1f}m" if distance else "?"
                            console.print(f"  Found grid pano: {metadata.pano_id} ({dist_str})")
                    
                except Exception:
                    continue
        
        # Breadth-first search through linked panoramas
        if not output_json and verbose:
            console.print(f"[dim]Traversing links up to depth {max_depth}...[/dim]")
        
        while to_check and len(panoramas_by_id) < max_results and len(checked_panos) < max_panos:
            pano_id, depth = to_check.popleft()
            
            # Stop if we've gone too deep
            if depth >= max_depth:
                continue
            
            try:
                metadata = downloader.get_metadata(pano_id=pano_id)
                
                # Explore linked panoramas
                if hasattr(metadata, 'links') and metadata.links:
                    for link in metadata.links:
                        if len(panoramas_by_id) >= max_results:
                            break
                        
                        linked_pano_id = link.get('panoId')
                        if linked_pano_id and linked_pano_id not in checked_panos:
                            checked_panos.add(linked_pano_id)
                            
                            try:
                                linked_metadata = downloader.get_metadata(pano_id=linked_pano_id)
                                
                                if linked_metadata.lat and linked_metadata.lng:
                                    distance = haversine_distance(
                                        lat, lng, linked_metadata.lat, linked_metadata.lng
                                    )
                                else:
                                    distance = None
                                
                                panoramas_by_id[linked_pano_id] = {
                                    'pano_id': linked_pano_id,
                                    'date': linked_metadata.date,
                                    'lat': linked_metadata.lat,
                                    'lng': linked_metadata.lng,
                                    'distance_m': round(distance, 1) if distance else None,
                                    'heading': linked_metadata.heading,
                                    'copyright': linked_metadata.copyright_info,
                                }
                                
                                # Add to queue for further traversal
                                to_check.append((linked_pano_id, depth + 1))
                                
                                if verbose and not output_json:
                                    console.print(f"  Found linked pano: {linked_pano_id} (depth {depth + 1})")
                                    
                            except Exception:
                                continue
                                
            except Exception:
                continue
        
        if verbose and not output_json:
            console.print(f"[dim]Checked {len(checked_panos)} total panoramas[/dim]")
        
    except Exception as e:
        raise click.ClickException(f"Query failed: {e}")
    
    if not panoramas_by_id:
        if output_json:
            click.echo(json.dumps({"error": "No panoramas found"}, indent=2))
        else:
            console.print("[yellow]No panoramas found at this location[/yellow]")
        sys.exit(1)
    
    # Sort by distance and limit results
    results = sorted(
        panoramas_by_id.values(),
        key=lambda x: x['distance_m'] if x['distance_m'] is not None else float('inf')
    )[:max_results]
    
    # Output results
    if output_json:
        output_data = {
            'query': {'lat': lat, 'lng': lng, 'radius': radius},
            'count': len(results),
            'panoramas': results
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        console.print(f"\n[bold]Found {len(results)} panorama(s):[/bold]\n")
        
        for i, pano in enumerate(results, 1):
            distance_str = f"{pano['distance_m']:.1f}m" if pano['distance_m'] is not None else "unknown"
            date_str = pano['date'] if pano['date'] else "unknown"
            coords_str = f"({pano['lat']:.6f}, {pano['lng']:.6f})" if pano['lat'] and pano['lng'] else "unknown"
            
            console.print(f"[bold]{i}.[/bold] {pano['pano_id']}")
            console.print(f"   [dim]Date:[/dim] {date_str}")
            console.print(f"   [dim]Distance:[/dim] {distance_str}")
            console.print(f"   [dim]Coordinates:[/dim] {coords_str}")
            
            if verbose and pano.get('heading') is not None:
                console.print(f"   [dim]Heading:[/dim] {pano['heading']:.1f}°")
            if verbose and pano.get('copyright'):
                console.print(f"   [dim]Copyright:[/dim] {pano['copyright']}")
            
            console.print()
        
        # Generate URL list for batch downloading
        console.print(f"[{accent}]URLs for batch download:[/{accent}]")
        url_list = []
        for pano in results:
            if pano['lat'] and pano['lng']:
                # Use format compatible with the download command parser
                # Pattern: !3m7!1e1!3m5!1s{pano_id}! (trailing ! is required)
                url = (
                    f"https://www.google.com/maps/@{pano['lat']},{pano['lng']},"
                    f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{pano['pano_id']}!"
                )
                url_list.append(url)

        
        # Save URL list to file
        url_filename = f"streetview_urls_{lat}_{lng}.txt"
        with open(url_filename, 'w') as f:
            f.write('\n'.join(url_list))
        
        console.print(f"  Saved {len(url_list)} URLs to: [bold]{url_filename}[/bold]")
        console.print(f"\n[{accent}]Batch download all panoramas:[/{accent}]")
        console.print(f"  streetview-dl --batch {url_filename} --output-dir ./panoramas/")
        
        # Show example for downloading single panorama
        if results:
            console.print(f"\n[{accent}]Download nearest panorama:[/{accent}]")
            nearest = results[0]
            console.print(f"  streetview-dl --output nearest.jpg \"{url_list[0]}\"")



def cli_dispatcher():
    """Route to appropriate command based on first argument."""
    import sys
    
    # Check if first argument is 'query'
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'query':
            # Remove 'query' from argv and call query_command
            sys.argv.pop(1)
            query_command()
            return
        elif cmd == 'help':
            # Show combined help overview
            click.echo("streetview-dl - Download high-resolution Google Street View panoramas\n")
            click.echo("Usage:")
            click.echo("  streetview-dl [OPTIONS] URL              Download a panorama from URL")
            click.echo("  streetview-dl query [OPTIONS]            Query panoramas by coordinates\n")
            click.echo("Commands:")
            click.echo("  streetview-dl --help                     Show download command help")
            click.echo("  streetview-dl query --help               Show query command help")
            click.echo("  streetview-dl --version                  Show version")
            return
    
    # Call main download command
    main()


if __name__ == "__main__":
    cli_dispatcher()

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
            clip=clip,
            crop_bottom=crop_bottom,
            no_crop=no_crop,
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
    clip: str,
    crop_bottom: float,
    no_crop: bool,
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
    """Process a single URL."""
    accent = resolve_accent(accent_color)
    start_time = time.perf_counter()

    # Handle --no-crop flag
    if no_crop:
        crop_bottom = 1.0

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
    downloader = StreetViewDownloader(
        api_key=api_key, timeout=timeout, retries=retries, backoff=backoff
    )

    # Extract panorama info
    pano_id, yaw, pitch, fov, mode_token = extract_from_maps_url(url)
    if not pano_id:
        raise click.ClickException("Could not extract panorama ID from URL")
    
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

    # Get metadata
    with console.status(f"[bold {accent}]Fetching metadata..."):
        street_view_metadata = downloader.get_metadata(pano_id=pano_id)
        street_view_metadata.url_yaw = yaw
        street_view_metadata.url_pitch = pitch
        street_view_metadata.url_fov = fov
        street_view_metadata.url_mode_token = mode_token

    if verbose:
        console.print(
            f"[dim]Resolution: {street_view_metadata.image_width}×{street_view_metadata.image_height}[/dim]"
        )
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
            pano_id, _, _, _, _ = extract_from_maps_url(url)
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


if __name__ == "__main__":
    main()

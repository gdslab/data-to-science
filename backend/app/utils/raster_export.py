import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

import rasterio

from app.utils.ColorBar import get_cmap
from app.utils.stac.STACProperties import (
    STACProperties,
    STACRasterProperties,
    Stats,
)

logger = logging.getLogger("__name__")


# Long edge of the exported image. Full resolution orthomosaics can exceed the
# JPEG format's 65535 pixel limit, so exports are always capped.
JPEG_MAX_DIMENSION = 4096
JPEG_QUALITY = 85
# Matches the fallback used by the map's symbology helpers.
DEFAULT_MIN_MAX: Tuple[float, float] = (0.0, 255.0)
# Number of entries written to the gdaldem color-relief table.
COLOR_TABLE_STEPS = 256
# Production runs the backend with a read-only root filesystem and a tmpfs
# mounted on /var/tmp only, so temporary files cannot use the /tmp default.
TEMP_DIR = "/var/tmp"
RGB_BANDS = ("red", "green", "blue")
# Total wall clock budget for the GDAL commands in one export, shared across all
# of them rather than applied per command. Two nginx layers sit in front of the
# API (the compose proxy and a host level nginx outside this repo) and both use
# nginx's 60s proxy_read_timeout default, so the export has to fail on its own
# before either of them cuts the connection and leaves GDAL running unattended.
# Measured exports take 1-3s, so this is roughly 15-30x the expected runtime.
EXPORT_TIMEOUT_SECONDS = 45.0
# Reading a raster at full resolution runs at roughly 80 megapixels per second
# for a compressed COG, so a raster past this size cannot finish inside the
# budget above without overviews to read instead. Anything arriving through the
# normal upload path has them, because convert_to_cog writes with -of COG, which
# builds a pyramid. Reaching this limit means the file was already in COG layout
# when it was uploaded and was moved into place without one.
MAX_PIXELS_WITHOUT_OVERVIEWS = 2_000_000_000


class RasterExportError(ValueError):
    """Base class for export failures that are not server faults.

    Subclasses ValueError so callers that already handle ValueError keep working.
    """


class RasterInputError(RasterExportError):
    """The raster itself cannot be exported.

    Raised when the file is missing, has no usable band metadata, or is too large
    to read without overviews. These point at the stored data rather than at
    anything the user chose, so callers should log them where operators will see
    them.
    """


class SymbologyError(RasterExportError):
    """The symbology settings cannot be applied to this raster.

    Raised for a colour ramp, band index, or value range the user can correct.
    """


class ExportDeadline:
    """Wall clock budget shared by every GDAL command in a single export.

    A per command timeout would not bound the export, because the single band
    path runs three commands in sequence. Handing each of them what is left of
    one budget keeps the total under the limit no matter how many run.
    """

    def __init__(self, seconds: float = EXPORT_TIMEOUT_SECONDS) -> None:
        self.seconds = seconds
        self._expires_at = time.monotonic() + seconds

    def remaining(self) -> float:
        """Returns the seconds left in the budget, never less than zero."""
        return max(0.0, self._expires_at - time.monotonic())


def create_export_work_dir() -> Path:
    """Creates a temporary directory for export intermediates and output.

    Returns:
        Path: Path to the new temporary directory.
    """
    return Path(tempfile.mkdtemp(dir=TEMP_DIR))


def export_raster_to_jpeg(
    in_raster: Path,
    out_jpeg: Path,
    stac_properties: STACProperties,
    symbology: Optional[dict] = None,
    max_dimension: int = JPEG_MAX_DIMENSION,
    work_dir: Optional[Path] = None,
    timeout: float = EXPORT_TIMEOUT_SECONDS,
) -> Path:
    """Converts a raster data product to a JPEG image.

    When symbology settings are provided, the color ramp, rescaling mode, and band
    composition chosen by the user are applied to the exported image. Without them,
    the raster bands are converted as-is using the statistics from its STAC
    properties.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_jpeg (Path): Path for the output JPEG image.
        stac_properties (STACProperties): STAC properties for the input raster.
        symbology (Optional[dict]): Symbology settings from the map. Defaults to None.
        max_dimension (int): Maximum length for the output's long edge.
        work_dir (Optional[Path]): Directory for intermediate files. Defaults to None.
        timeout (float): Wall clock budget shared by every GDAL command.

    Raises:
        RasterInputError: Input raster or its band metadata is missing or unusable.
        SymbologyError: Symbology settings cannot be applied to this raster.
        RuntimeError: A GDAL command failed or ran out of time.

    Returns:
        Path: Path to the output JPEG image.
    """
    in_raster = Path(in_raster)
    out_jpeg = Path(out_jpeg)

    if not in_raster.exists():
        raise RasterInputError("Input raster not found")

    # stac_properties is nullable on the data product record, so a product whose
    # initial processing never finished can reach this with nothing to read
    bands = stac_properties.get("raster") or [] if stac_properties else []
    if len(bands) == 0:
        raise RasterInputError("Raster band metadata is missing")

    deadline = ExportDeadline(timeout)
    outsize_params = get_outsize_params(in_raster, max_dimension)

    # The settings' own shape picks the path, not the raster's band count: only
    # single band settings carry a color ramp, and only multiband settings carry a
    # band composition. Going by band count instead would reject a color ramp
    # applied to a raster that happens to have more than one band, which is what a
    # user style saved before the band count changed looks like.
    if not symbology:
        export_without_symbology(
            in_raster, out_jpeg, stac_properties, outsize_params, deadline
        )
    elif "colorRamp" in symbology:
        export_single_band(
            in_raster,
            out_jpeg,
            stac_properties,
            symbology,
            outsize_params,
            work_dir,
            deadline,
        )
    elif any(band_name in symbology for band_name in RGB_BANDS):
        export_multiband(
            in_raster, out_jpeg, stac_properties, symbology, outsize_params, deadline
        )
    else:
        raise SymbologyError(
            "Symbology settings must include a color ramp or a band composition"
        )

    return out_jpeg


def export_without_symbology(
    in_raster: Path,
    out_jpeg: Path,
    stac_properties: STACProperties,
    outsize_params: List[str],
    deadline: Optional[ExportDeadline] = None,
) -> None:
    """Converts a raster to JPEG using the statistics from its STAC properties.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_jpeg (Path): Path for the output JPEG image.
        stac_properties (STACProperties): STAC properties for the input raster.
        outsize_params (List[str]): gdal_translate parameters for resizing.
        deadline (Optional[ExportDeadline]): Shared budget for GDAL commands.
    """
    bands = stac_properties["raster"]

    if len(bands) > 2:
        band_indexes = [1, 2, 3]
        ranges = [get_stats_min_max(band) for band in bands[:3]]
    else:
        band_indexes = [1]
        ranges = [get_stats_min_max(bands[0])]

    run_jpeg_translate(
        in_raster, out_jpeg, band_indexes, ranges, outsize_params, deadline
    )


def export_multiband(
    in_raster: Path,
    out_jpeg: Path,
    stac_properties: STACProperties,
    symbology: dict,
    outsize_params: List[str],
    deadline: Optional[ExportDeadline] = None,
) -> None:
    """Converts a multiband raster to JPEG using the user's band composition.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_jpeg (Path): Path for the output JPEG image.
        stac_properties (STACProperties): STAC properties for the input raster.
        symbology (dict): Multiband symbology settings from the map.
        outsize_params (List[str]): gdal_translate parameters for resizing.
        deadline (Optional[ExportDeadline]): Shared budget for GDAL commands.

    Raises:
        SymbologyError: A band index is missing or out of range.
    """
    band_count = len(stac_properties["raster"])
    band_indexes = []

    for band_name in RGB_BANDS:
        band = symbology.get(band_name)
        band_index = band.get("idx") if isinstance(band, dict) else None
        if not isinstance(band_index, int) or band_index < 1 or band_index > band_count:
            raise SymbologyError(f"Invalid band index for {band_name} band")
        band_indexes.append(band_index)

    ranges = resolve_multiband_ranges(stac_properties, symbology)

    run_jpeg_translate(
        in_raster, out_jpeg, band_indexes, ranges, outsize_params, deadline
    )


def export_single_band(
    in_raster: Path,
    out_jpeg: Path,
    stac_properties: STACProperties,
    symbology: dict,
    outsize_params: List[str],
    work_dir: Optional[Path] = None,
    deadline: Optional[ExportDeadline] = None,
) -> None:
    """Converts a single band raster to JPEG using the user's color ramp.

    The raster is resized first so the color ramp and JPEG conversion both run
    against a small image. gdaldem color-relief applies the ramp in the raster's
    native units, so the resize must not rescale pixel values.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_jpeg (Path): Path for the output JPEG image.
        stac_properties (STACProperties): STAC properties for the input raster.
        symbology (dict): Single band symbology settings from the map.
        outsize_params (List[str]): gdal_translate parameters for resizing.
        work_dir (Optional[Path]): Directory for intermediate files. Defaults to None.
        deadline (Optional[ExportDeadline]): Shared budget for GDAL commands.

    Raises:
        SymbologyError: Color ramp is missing from the symbology settings.
        RuntimeError: A GDAL command failed or ran out of time.
    """
    color_ramp = symbology.get("colorRamp")
    if not color_ramp:
        raise SymbologyError("Color ramp missing from symbology settings")

    minimum, maximum = resolve_single_band_range(stac_properties, symbology)
    color_table = build_color_table(color_ramp, minimum, maximum)

    temp_dir_created = work_dir is None
    if work_dir is None:
        work_dir = create_export_work_dir()
    else:
        work_dir = Path(work_dir)

    try:
        scaled_raster = work_dir / "scaled.tif"
        color_table_path = work_dir / "color_table.txt"
        relief_raster = work_dir / "relief.tif"

        color_table_path.write_text(color_table)

        # Resize while preserving the raster's native values and data type
        translate_command = [
            "gdal_translate",
            "-b",
            "1",
            "-of",
            "GTiff",
            "-r",
            "average",
        ]
        translate_command.extend(outsize_params)

        nodata = symbology.get("nodata")
        if nodata is not None:
            translate_command.extend(["-a_nodata", str(nodata)])

        translate_command.extend([str(in_raster), str(scaled_raster)])
        run_gdal_command(
            translate_command, "Failed to prepare raster for color ramp", deadline
        )

        # Apply the color ramp, producing a three band RGB raster
        run_gdal_command(
            [
                "gdaldem",
                "color-relief",
                str(scaled_raster),
                str(color_table_path),
                str(relief_raster),
                "-of",
                "GTiff",
            ],
            "Failed to apply color ramp to raster",
            deadline,
        )

        run_gdal_command(
            [
                "gdal_translate",
                "-of",
                "JPEG",
                "-co",
                f"QUALITY={JPEG_QUALITY}",
                str(relief_raster),
                str(out_jpeg),
            ],
            "Failed to convert raster to JPEG",
            deadline,
        )
    finally:
        if temp_dir_created:
            shutil.rmtree(work_dir, ignore_errors=True)


def build_color_table(
    colormap_name: str,
    vmin: float,
    vmax: float,
    steps: int = COLOR_TABLE_STEPS,
) -> str:
    """Builds a gdaldem color-relief table for a matplotlib color ramp.

    The ramp is sampled at evenly spaced points across the value range. gdaldem
    interpolates between entries and clamps values outside the range, matching how
    the map renders the same color ramp. The "nv" entry keeps nodata pixels black,
    since the JPEG format has no alpha channel.

    Args:
        colormap_name (str): Name of the matplotlib color ramp.
        vmin (float): Value mapped to the start of the color ramp.
        vmax (float): Value mapped to the end of the color ramp.
        steps (int): Number of color entries to write.

    Raises:
        SymbologyError: Value range or step count is invalid, or the ramp is unknown.

    Returns:
        str: Contents of the color table file.
    """
    if steps < 2:
        raise SymbologyError("Color table must have at least two steps")

    if vmin > vmax:
        raise SymbologyError("Minimum value cannot be greater than maximum value")

    if vmin == vmax:
        # Avoid a degenerate table where every entry lands on the same value. A
        # fixed epsilon is a no-op at large magnitudes, because the spacing
        # between representable floats there is wider than the epsilon itself
        # (1e10 + 1e-6 rounds straight back to 1e10), so scale the span with the
        # value and keep a floor for values at or near zero.
        vmax = vmin + max(abs(vmin) * 1e-9, 1e-9)

    try:
        colormap = get_cmap(colormap_name)
    except ValueError as e:
        # The ramp name comes from the user's map settings, so an unknown one is
        # something they can correct rather than a server fault
        raise SymbologyError(f"Unknown color ramp: {colormap_name}") from e

    lines = []
    for step in range(steps):
        fraction = step / (steps - 1)
        value = vmin + (vmax - vmin) * fraction
        red, green, blue, _ = colormap(fraction)
        lines.append(
            f"{value} {round(red * 255)} {round(green * 255)} {round(blue * 255)}"
        )

    lines.append("nv 0 0 0")

    return "\n".join(lines) + "\n"


def resolve_single_band_range(
    stac_properties: STACProperties, symbology: dict
) -> Tuple[float, float]:
    """Returns the min/max values used to rescale a single band raster.

    Mirrors the map's getSingleBandMinMax helper so exports match what the user
    sees on the map.

    Args:
        stac_properties (STACProperties): STAC properties for the input raster.
        symbology (dict): Single band symbology settings from the map.

    Returns:
        Tuple[float, float]: Min and max values for the band.
    """
    mode = symbology.get("mode")

    if mode == "minMax" or mode == "userDefined":
        min_key, max_key = (
            ("min", "max") if mode == "minMax" else ("userMin", "userMax")
        )
        minimum = symbology.get(min_key)
        maximum = symbology.get(max_key)
        if minimum is None or maximum is None:
            logger.warning(
                f"Symbology missing {min_key}/{max_key}, "
                "falling back to default min/max"
            )
            return DEFAULT_MIN_MAX
        return float(minimum), float(maximum)

    if mode == "meanStdDev":
        stats = get_band_stats(stac_properties, 1)
        if stats is None:
            logger.warning("Stats missing, falling back to default min/max")
            return DEFAULT_MIN_MAX
        deviation = float(stats["stddev"]) * float(symbology.get("meanStdDev", 2))
        mean = float(stats["mean"])
        return mean - deviation, mean + deviation

    logger.warning(f"Unexpected symbology mode: {mode}")
    return DEFAULT_MIN_MAX


def resolve_multiband_ranges(
    stac_properties: STACProperties, symbology: dict
) -> List[Tuple[float, float]]:
    """Returns the min/max values used to rescale each band of a multiband raster.

    Mirrors the map's getMultibandMinMax helper, including its all-or-nothing
    fallback when any of the three bands is missing values. In meanStdDev mode the
    stats are looked up by the band index the user selected, so swapping bands
    changes the values used.

    Args:
        stac_properties (STACProperties): STAC properties for the input raster.
        symbology (dict): Multiband symbology settings from the map.

    Returns:
        List[Tuple[float, float]]: Min and max values for the red, green, and blue
            bands, in that order.
    """
    default_ranges = [DEFAULT_MIN_MAX, DEFAULT_MIN_MAX, DEFAULT_MIN_MAX]

    bands: List[dict] = []
    for band_name in RGB_BANDS:
        band = symbology.get(band_name)
        if not isinstance(band, dict):
            logger.warning(
                "Symbology missing at least one band, falling back to default min/max"
            )
            return default_ranges
        bands.append(band)

    mode = symbology.get("mode")

    if mode == "minMax" or mode == "userDefined":
        min_key, max_key = (
            ("min", "max") if mode == "minMax" else ("userMin", "userMax")
        )
        if not all(
            band.get(min_key) is not None and band.get(max_key) is not None
            for band in bands
        ):
            logger.warning(
                f"Symbology missing {min_key}/{max_key} for at least one band, "
                "falling back to default min/max"
            )
            return default_ranges
        return [(float(band[min_key]), float(band[max_key])) for band in bands]

    if mode == "meanStdDev":
        deviations = float(symbology.get("meanStdDev", 2))
        ranges = []
        for band in bands:
            stats = get_band_stats(stac_properties, band.get("idx"))
            if stats is None:
                logger.warning(
                    "Stats missing for at least one band, "
                    "falling back to default min/max"
                )
                return default_ranges
            deviation = float(stats["stddev"]) * deviations
            mean = float(stats["mean"])
            ranges.append((mean - deviation, mean + deviation))
        return ranges

    logger.warning(f"Unexpected symbology mode: {mode}")
    return default_ranges


def get_band_stats(stac_properties: STACProperties, band_index: Any) -> Optional[Stats]:
    """Returns the stats for a one-based band index, or None when unavailable.

    Args:
        stac_properties (STACProperties): STAC properties for the input raster.
        band_index (Any): One-based band index.

    Returns:
        Optional[Stats]: Band stats with a mean and standard deviation.
    """
    if not isinstance(band_index, int) or band_index < 1:
        return None

    bands = stac_properties.get("raster") or []
    if band_index > len(bands):
        return None

    stats = bands[band_index - 1].get("stats")
    if not stats or stats.get("mean") is None or stats.get("stddev") is None:
        return None

    return stats


def get_stats_min_max(band: STACRasterProperties) -> Tuple[float, float]:
    """Returns the min/max values recorded in a band's STAC stats.

    Args:
        band (STACRasterProperties): STAC raster band properties.

    Returns:
        Tuple[float, float]: Min and max values for the band.
    """
    stats = band.get("stats") or {}
    minimum = stats.get("minimum")
    maximum = stats.get("maximum")

    if minimum is None or maximum is None:
        logger.warning("Band stats missing, falling back to default min/max")
        return DEFAULT_MIN_MAX

    return float(minimum), float(maximum)


def get_outsize_params(in_raster: Path, max_dimension: int) -> List[str]:
    """Returns gdal_translate parameters that cap the raster's long edge.

    Args:
        in_raster (Path): Path to input raster dataset.
        max_dimension (int): Maximum length for the output's long edge.

    Raises:
        RasterInputError: The raster is too large to read without overviews.
        RuntimeError: The raster could not be read.

    Returns:
        List[str]: gdal_translate parameters, empty when no resizing is needed.
    """
    if max_dimension <= 0:
        return []

    try:
        with rasterio.open(in_raster) as src:
            width, height = src.width, src.height
            # Read while the dataset is open so the overview check below costs
            # nothing extra
            overviews = src.overviews(1) if src.count else []
    except rasterio.errors.RasterioIOError as e:
        raise RuntimeError(f"Failed to read raster dimensions: {e}") from e

    if max(width, height) <= max_dimension:
        return []

    # Downsampling reads the smallest overview at or above the target size, which
    # keeps the work bounded no matter how large the source is. Without a
    # pyramid, GDAL has to read every pixel instead, and past this size that
    # cannot finish inside the export budget. Fail now rather than burning the
    # whole budget first, because nothing rate limits repeated attempts.
    if not overviews and width * height > MAX_PIXELS_WITHOUT_OVERVIEWS:
        raise RasterInputError(
            f"Raster is {width}x{height} with no overviews, too large to export"
        )

    if width >= height:
        return ["-outsize", str(max_dimension), "0"]

    return ["-outsize", "0", str(max_dimension)]


def run_jpeg_translate(
    in_raster: Path,
    out_jpeg: Path,
    band_indexes: List[int],
    ranges: List[Tuple[float, float]],
    outsize_params: List[str],
    deadline: Optional[ExportDeadline] = None,
) -> None:
    """Runs gdal_translate to write a JPEG with the given bands and value ranges.

    Args:
        in_raster (Path): Path to input raster dataset.
        out_jpeg (Path): Path for the output JPEG image.
        band_indexes (List[int]): One-based band indexes to include, in output order.
        ranges (List[Tuple[float, float]]): Min/max values for each output band.
        outsize_params (List[str]): gdal_translate parameters for resizing.
        deadline (Optional[ExportDeadline]): Shared budget for GDAL commands.

    Raises:
        RuntimeError: gdal_translate failed or ran out of time.
    """
    command = [
        "gdal_translate",
        "-of",
        "JPEG",
        "-ot",
        "Byte",
        "-co",
        f"QUALITY={JPEG_QUALITY}",
        "-r",
        "average",
    ]

    for band_index in band_indexes:
        command.extend(["-b", str(band_index)])

    command.extend(outsize_params)

    # -scale_N refers to the output band position, not the source band
    for position, (minimum, maximum) in enumerate(ranges, start=1):
        command.extend([f"-scale_{position}", str(minimum), str(maximum), "0", "255"])

    command.extend([str(in_raster), str(out_jpeg)])

    run_gdal_command(command, "Failed to convert raster to JPEG", deadline)


def run_gdal_command(
    command: List[str],
    error_message: str,
    deadline: Optional[ExportDeadline] = None,
) -> None:
    """Runs a GDAL command and raises a RuntimeError when it fails.

    When a deadline is given, the command gets whatever is left of the export's
    shared budget, and subprocess.run kills it if that runs out. Without one the
    command is unbounded, which is only appropriate off the request path.

    Args:
        command (List[str]): Command and arguments to run.
        error_message (str): Message prefix used when the command fails.
        deadline (Optional[ExportDeadline]): Shared budget for GDAL commands.

    Raises:
        RuntimeError: The command failed, or the budget ran out.
    """
    timeout = deadline.remaining() if deadline else None

    if deadline and timeout is not None and timeout <= 0:
        raise RuntimeError(
            f"{error_message}: export exceeded its {deadline.seconds:g}s budget"
        )

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        budget = deadline.seconds if deadline else 0
        raise RuntimeError(
            f"{error_message}: export exceeded its {budget:g}s budget"
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{error_message}: {e.stderr.decode('utf-8')}") from e

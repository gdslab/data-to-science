import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Sequence, Tuple
from unittest.mock import patch

import numpy as np
import pytest
import rasterio

from app.tests.utils.data_product import test_stac_props_dsm
from app.utils import raster_export
from app.utils.ColorBar import get_cmap
from app.utils.ImageProcessor import get_info, get_stac_properties
from app.utils.raster_export import (
    DEFAULT_MIN_MAX,
    RasterInputError,
    SymbologyError,
    build_color_table,
    export_raster_to_jpeg,
    resolve_multiband_ranges,
    resolve_single_band_range,
)

single_band_dataset = Path("/app/app/tests/data/test.tif")
multiband_dataset = Path("/app/app/tests/data/test_multispectral.tif")


@pytest.fixture(scope="module")
def multiband_stac_properties() -> Dict[str, Any]:
    """STAC properties for the multiband test dataset.

    The multiband fixture in app.tests.utils.data_product only describes a single
    raster band, so the properties are read from the dataset itself. The dataset is
    copied first so gdalinfo cannot update the sidecar file kept in version control.
    """
    with TemporaryDirectory() as tmpdir:
        raster = Path(tmpdir) / multiband_dataset.name
        shutil.copyfile(multiband_dataset, raster)

        sidecar = Path(f"{multiband_dataset}.aux.xml")
        if sidecar.exists():
            shutil.copyfile(sidecar, Path(f"{raster}.aux.xml"))

        return get_stac_properties(get_info(raster))


def create_single_band_symbology(**overrides: Any) -> Dict[str, Any]:
    """Returns single band symbology settings matching the map's defaults."""
    stats = test_stac_props_dsm["raster"][0]["stats"]
    symbology: Dict[str, Any] = {
        "colorRamp": "viridis",
        "meanStdDev": 2,
        "mode": "minMax",
        "opacity": 100,
        "min": stats["minimum"],
        "max": stats["maximum"],
        "userMin": stats["minimum"],
        "userMax": stats["maximum"],
    }
    symbology.update(overrides)
    return symbology


def create_multiband_symbology(
    stac_properties: Dict[str, Any],
    band_indexes: Sequence[int] = (1, 2, 3),
    **overrides: Any,
) -> Dict[str, Any]:
    """Returns multiband symbology settings matching the map's defaults."""
    symbology: Dict[str, Any] = {"meanStdDev": 2, "mode": "minMax", "opacity": 100}

    for band_name, band_index in zip(("red", "green", "blue"), band_indexes):
        stats = stac_properties["raster"][band_index - 1]["stats"]
        symbology[band_name] = {
            "idx": band_index,
            "min": stats["minimum"],
            "max": stats["maximum"],
            "userMin": stats["minimum"],
            "userMax": stats["maximum"],
        }

    symbology.update(overrides)
    return symbology


def read_jpeg(out_jpeg: Path) -> Tuple[str, int, Tuple[int, int], np.ndarray]:
    """Returns the driver, band count, dimensions, and pixels of an exported image."""
    with rasterio.open(out_jpeg) as src:
        assert all(dtype == "uint8" for dtype in src.dtypes)
        return src.driver, src.count, (src.width, src.height), src.read()


def test_resolve_single_band_range_uses_min_max_mode() -> None:
    """Min/max mode uses the min and max recorded in the symbology settings."""
    symbology = create_single_band_symbology(mode="minMax", min=1.5, max=9.5)

    assert resolve_single_band_range(test_stac_props_dsm, symbology) == (1.5, 9.5)


def test_resolve_single_band_range_uses_user_defined_mode() -> None:
    """User defined mode uses the user's min and max, not the raster's."""
    symbology = create_single_band_symbology(
        mode="userDefined", min=1.5, max=9.5, userMin=3.0, userMax=4.0
    )

    assert resolve_single_band_range(test_stac_props_dsm, symbology) == (3.0, 4.0)


def test_resolve_single_band_range_uses_mean_std_dev_mode() -> None:
    """Mean/standard deviation mode derives the range from the band's stats."""
    stats = test_stac_props_dsm["raster"][0]["stats"]
    symbology = create_single_band_symbology(mode="meanStdDev", meanStdDev=2)

    minimum, maximum = resolve_single_band_range(test_stac_props_dsm, symbology)

    deviation = stats["stddev"] * 2
    assert minimum == pytest.approx(stats["mean"] - deviation)
    assert maximum == pytest.approx(stats["mean"] + deviation)


def test_resolve_single_band_range_falls_back_when_values_missing() -> None:
    """Missing min/max values fall back to the default range."""
    symbology = create_single_band_symbology(mode="minMax")
    symbology.pop("max")

    assert resolve_single_band_range(test_stac_props_dsm, symbology) == DEFAULT_MIN_MAX


def test_resolve_single_band_range_falls_back_on_unknown_mode() -> None:
    """An unrecognized mode falls back to the default range."""
    symbology = create_single_band_symbology(mode="notARealMode")

    assert resolve_single_band_range(test_stac_props_dsm, symbology) == DEFAULT_MIN_MAX


def test_resolve_multiband_ranges_uses_min_max_mode(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """Min/max mode uses each band's recorded min and max."""
    symbology = create_multiband_symbology(multiband_stac_properties)

    ranges = resolve_multiband_ranges(multiband_stac_properties, symbology)

    expected = [
        (
            multiband_stac_properties["raster"][index]["stats"]["minimum"],
            multiband_stac_properties["raster"][index]["stats"]["maximum"],
        )
        for index in range(3)
    ]
    assert ranges == expected


def test_resolve_multiband_ranges_uses_user_defined_mode(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """User defined mode uses each band's user min and max."""
    symbology = create_multiband_symbology(
        multiband_stac_properties, mode="userDefined"
    )
    for band_name in ("red", "green", "blue"):
        symbology[band_name]["userMin"] = 100.0
        symbology[band_name]["userMax"] = 200.0

    ranges = resolve_multiband_ranges(multiband_stac_properties, symbology)

    assert ranges == [(100.0, 200.0), (100.0, 200.0), (100.0, 200.0)]


def test_resolve_multiband_ranges_reads_stats_by_band_index(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """Mean/standard deviation mode reads stats for the band the user selected."""
    symbology = create_multiband_symbology(
        multiband_stac_properties, band_indexes=(4, 5, 6), mode="meanStdDev"
    )

    ranges = resolve_multiband_ranges(multiband_stac_properties, symbology)

    for position, band_index in enumerate((4, 5, 6)):
        stats = multiband_stac_properties["raster"][band_index - 1]["stats"]
        deviation = stats["stddev"] * 2
        assert ranges[position][0] == pytest.approx(stats["mean"] - deviation)
        assert ranges[position][1] == pytest.approx(stats["mean"] + deviation)


def test_resolve_multiband_ranges_falls_back_when_a_band_is_incomplete(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """A single band missing a value falls all three bands back to the default."""
    symbology = create_multiband_symbology(multiband_stac_properties)
    symbology["blue"].pop("max")

    ranges = resolve_multiband_ranges(multiband_stac_properties, symbology)

    assert ranges == [DEFAULT_MIN_MAX, DEFAULT_MIN_MAX, DEFAULT_MIN_MAX]


def test_build_color_table_spans_the_value_range() -> None:
    """The color table covers the range in ascending order using the ramp's colors."""
    color_table = build_color_table("viridis", 10.0, 20.0, steps=8)

    lines = color_table.strip().split("\n")
    assert lines[-1] == "nv 0 0 0"

    entries = [line.split(" ") for line in lines[:-1]]
    values = [float(entry[0]) for entry in entries]
    assert len(values) == 8
    assert values == sorted(values)
    assert values[0] == pytest.approx(10.0)
    assert values[-1] == pytest.approx(20.0)

    colormap = get_cmap("viridis")
    for fraction, entry in zip((0.0, 1.0), (entries[0], entries[-1])):
        red, green, blue, _ = colormap(fraction)
        expected = [round(red * 255), round(green * 255), round(blue * 255)]
        assert [int(value) for value in entry[1:]] == expected


def test_build_color_table_handles_a_flat_value_range() -> None:
    """An empty range still produces a usable table with distinct values."""
    color_table = build_color_table("viridis", 5.0, 5.0, steps=4)

    values = [
        float(line.split(" ")[0]) for line in color_table.strip().split("\n")[:-1]
    ]
    assert len(values) == len(set(values))


def test_build_color_table_rejects_an_inverted_value_range() -> None:
    """A min greater than the max is rejected."""
    with pytest.raises(ValueError):
        build_color_table("viridis", 20.0, 10.0)


def test_build_color_table_rejects_an_unknown_color_ramp() -> None:
    """An unrecognized color ramp name is rejected."""
    with pytest.raises(ValueError):
        build_color_table("notARealColorRamp", 10.0, 20.0)


def test_get_cmap_rejects_an_unknown_color_ramp() -> None:
    """get_cmap raises a ValueError rather than leaking an UnboundLocalError."""
    with pytest.raises(ValueError):
        get_cmap("notARealColorRamp")


def test_export_without_symbology_converts_a_single_band_raster() -> None:
    """A single band raster exports as a single band JPEG."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(single_band_dataset, out_jpeg, test_stac_props_dsm)

        driver, band_count, dimensions, _ = read_jpeg(out_jpeg)
        assert driver == "JPEG"
        assert band_count == 1
        assert dimensions == (203, 240)


def test_export_without_symbology_converts_a_multiband_raster(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """A multiband raster exports as a three band JPEG."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(multiband_dataset, out_jpeg, multiband_stac_properties)

        driver, band_count, _, _ = read_jpeg(out_jpeg)
        assert driver == "JPEG"
        assert band_count == 3


def test_export_with_symbology_applies_the_color_ramp() -> None:
    """A single band raster with symbology exports as an RGB JPEG using the ramp."""
    with rasterio.open(single_band_dataset) as src:
        band = src.read(1, masked=True)

    lowest_row, lowest_column = np.unravel_index(np.ma.argmin(band), band.shape)
    nodata_row, nodata_column = np.unravel_index(
        np.argmax(np.ma.getmaskarray(band)), band.shape
    )

    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            single_band_dataset,
            out_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(colorRamp="viridis"),
        )

        driver, band_count, _, pixels = read_jpeg(out_jpeg)
        assert driver == "JPEG"
        assert band_count == 3

        # The lowest value in the raster takes the color at the start of the ramp.
        # JPEG is lossy, so the comparison allows for compression artifacts.
        red, green, blue, _ = get_cmap("viridis")(0.0)
        expected = np.array([round(red * 255), round(green * 255), round(blue * 255)])
        actual = pixels[:, lowest_row, lowest_column].astype(int)
        assert np.all(np.abs(actual - expected) <= 20)

        # Nodata has no color ramp entry, so it renders darker than the ramp's start
        nodata_pixel = pixels[:, nodata_row, nodata_column].astype(int)
        assert nodata_pixel.sum() < expected.sum()


def test_export_with_symbology_honors_the_selected_color_ramp() -> None:
    """Two different color ramps produce two different images."""
    with TemporaryDirectory() as tmpdir:
        viridis_jpeg = Path(tmpdir) / "viridis.jpg"
        rainbow_jpeg = Path(tmpdir) / "rainbow.jpg"

        for out_jpeg, color_ramp in (
            (viridis_jpeg, "viridis"),
            (rainbow_jpeg, "rainbow"),
        ):
            export_raster_to_jpeg(
                single_band_dataset,
                out_jpeg,
                test_stac_props_dsm,
                symbology=create_single_band_symbology(colorRamp=color_ramp),
            )

        assert not np.array_equal(
            read_jpeg(viridis_jpeg)[3], read_jpeg(rainbow_jpeg)[3]
        )


def test_export_with_symbology_honors_the_rescaling_mode() -> None:
    """A narrower user defined range produces a different image than min/max."""
    with TemporaryDirectory() as tmpdir:
        min_max_jpeg = Path(tmpdir) / "min_max.jpg"
        user_defined_jpeg = Path(tmpdir) / "user_defined.jpg"

        stats = test_stac_props_dsm["raster"][0]["stats"]
        export_raster_to_jpeg(
            single_band_dataset,
            min_max_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(mode="minMax"),
        )
        export_raster_to_jpeg(
            single_band_dataset,
            user_defined_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(
                mode="userDefined",
                userMin=stats["mean"],
                userMax=stats["maximum"],
            ),
        )

        assert not np.array_equal(
            read_jpeg(min_max_jpeg)[3], read_jpeg(user_defined_jpeg)[3]
        )


def test_export_with_symbology_honors_the_band_composition(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """Swapping the red and blue band indexes produces a different image."""
    with TemporaryDirectory() as tmpdir:
        default_jpeg = Path(tmpdir) / "default.jpg"
        swapped_jpeg = Path(tmpdir) / "swapped.jpg"

        for out_jpeg, band_indexes in (
            (default_jpeg, (1, 2, 3)),
            (swapped_jpeg, (3, 2, 1)),
        ):
            export_raster_to_jpeg(
                multiband_dataset,
                out_jpeg,
                multiband_stac_properties,
                symbology=create_multiband_symbology(
                    multiband_stac_properties, band_indexes=band_indexes
                ),
            )

        assert not np.array_equal(
            read_jpeg(default_jpeg)[3], read_jpeg(swapped_jpeg)[3]
        )


def test_export_with_symbology_honors_multiband_rescaling(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """A narrower user defined range produces a different multiband image."""
    with TemporaryDirectory() as tmpdir:
        min_max_jpeg = Path(tmpdir) / "min_max.jpg"
        user_defined_jpeg = Path(tmpdir) / "user_defined.jpg"

        user_defined_symbology = create_multiband_symbology(
            multiband_stac_properties, mode="userDefined"
        )
        for band_name in ("red", "green", "blue"):
            stats = user_defined_symbology[band_name]
            stats["userMin"] = stats["min"]
            stats["userMax"] = (stats["min"] + stats["max"]) / 2

        export_raster_to_jpeg(
            multiband_dataset,
            min_max_jpeg,
            multiband_stac_properties,
            symbology=create_multiband_symbology(multiband_stac_properties),
        )
        export_raster_to_jpeg(
            multiband_dataset,
            user_defined_jpeg,
            multiband_stac_properties,
            symbology=user_defined_symbology,
        )

        assert not np.array_equal(
            read_jpeg(min_max_jpeg)[3], read_jpeg(user_defined_jpeg)[3]
        )


def test_export_with_symbology_accepts_a_nodata_value() -> None:
    """A nodata value in the symbology settings does not break the export."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            single_band_dataset,
            out_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(nodata=-9999),
        )

        driver, band_count, _, _ = read_jpeg(out_jpeg)
        assert driver == "JPEG"
        assert band_count == 3


def test_export_caps_the_long_edge() -> None:
    """A raster larger than the maximum dimension is resized, preserving its shape."""
    with TemporaryDirectory() as tmpdir:
        raw_jpeg = Path(tmpdir) / "raw.jpg"
        styled_jpeg = Path(tmpdir) / "styled.jpg"

        export_raster_to_jpeg(
            single_band_dataset, raw_jpeg, test_stac_props_dsm, max_dimension=8
        )
        export_raster_to_jpeg(
            single_band_dataset,
            styled_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(),
            max_dimension=8,
        )

        # test.tif is 203x240, so height is the long edge
        for out_jpeg in (raw_jpeg, styled_jpeg):
            width, height = read_jpeg(out_jpeg)[2]
            assert height == 8
            assert 0 < width <= 8


def test_export_does_not_resize_a_small_raster() -> None:
    """A raster within the maximum dimension keeps its original size."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            single_band_dataset,
            out_jpeg,
            test_stac_props_dsm,
            symbology=create_single_band_symbology(),
            max_dimension=4096,
        )

        assert read_jpeg(out_jpeg)[2] == (203, 240)


def test_export_rejects_an_out_of_range_band_index(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """A band index beyond the raster's band count is rejected."""
    symbology = create_multiband_symbology(multiband_stac_properties)
    symbology["red"]["idx"] = 99

    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            export_raster_to_jpeg(
                multiband_dataset,
                Path(tmpdir) / "export.jpg",
                multiband_stac_properties,
                symbology=symbology,
            )


def test_export_rejects_symbology_without_a_color_ramp() -> None:
    """Single band symbology missing its color ramp is rejected."""
    symbology = create_single_band_symbology()
    symbology.pop("colorRamp")

    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            export_raster_to_jpeg(
                single_band_dataset,
                Path(tmpdir) / "export.jpg",
                test_stac_props_dsm,
                symbology=symbology,
            )


def test_export_rejects_a_missing_raster() -> None:
    """A missing input raster is rejected."""
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            export_raster_to_jpeg(
                Path(tmpdir) / "does_not_exist.tif",
                Path(tmpdir) / "export.jpg",
                test_stac_props_dsm,
            )


def test_export_raises_for_an_unreadable_raster() -> None:
    """A file that is not a raster raises a runtime error."""
    with TemporaryDirectory() as tmpdir:
        not_a_raster = Path(tmpdir) / "not_a_raster.tif"
        not_a_raster.write_text("this is not a raster")

        with pytest.raises(RuntimeError):
            export_raster_to_jpeg(
                not_a_raster, Path(tmpdir) / "export.jpg", test_stac_props_dsm
            )


def test_export_rejects_missing_stac_properties() -> None:
    """A data product with no band metadata at all is rejected, not crashed on.

    stac_properties is nullable on the record, so a product whose initial
    processing never finished reaches the export with nothing to read.
    """
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(RasterInputError):
            export_raster_to_jpeg(
                single_band_dataset,
                Path(tmpdir) / "export.jpg",
                None,  # type: ignore[arg-type]
            )


def test_export_shares_one_timeout_budget_across_commands() -> None:
    """The single band path spends one budget across its three GDAL commands.

    A per command timeout would not bound the export: three commands at 45s each
    would allow 135s, well past the proxy timeout the budget exists to stay under.
    """
    timeouts: list = []
    run_command = subprocess.run

    def record(command: Any, **kwargs: Any) -> Any:
        timeouts.append(kwargs.get("timeout"))
        return run_command(command, **kwargs)

    with TemporaryDirectory() as tmpdir:
        with patch("app.utils.raster_export.subprocess.run", side_effect=record):
            export_raster_to_jpeg(
                single_band_dataset,
                Path(tmpdir) / "export.jpg",
                test_stac_props_dsm,
                symbology=create_single_band_symbology(),
                timeout=30,
            )

    assert len(timeouts) == 3
    assert all(timeout is not None and 0 < timeout <= 30 for timeout in timeouts)
    # each command gets what is left, so the budget only ever shrinks
    assert timeouts == sorted(timeouts, reverse=True)


def test_export_stops_when_the_timeout_budget_runs_out() -> None:
    """An export that outruns its budget fails instead of running unattended."""
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(RuntimeError, match="budget"):
            export_raster_to_jpeg(
                single_band_dataset,
                Path(tmpdir) / "export.jpg",
                test_stac_props_dsm,
                symbology=create_single_band_symbology(),
                timeout=0.001,
            )


def test_export_rejects_a_large_raster_without_overviews() -> None:
    """Downsampling a large raster with no pyramid is refused up front.

    Without overviews GDAL reads every pixel, which cannot finish inside the
    budget. The test raster is small, so the limit is lowered to reach the same
    guard a huge raster without overviews would hit.
    """
    with TemporaryDirectory() as tmpdir:
        with patch.object(raster_export, "MAX_PIXELS_WITHOUT_OVERVIEWS", 100):
            with pytest.raises(RasterInputError, match="no overviews"):
                export_raster_to_jpeg(
                    single_band_dataset,
                    Path(tmpdir) / "export.jpg",
                    test_stac_props_dsm,
                    max_dimension=8,
                )


def test_export_allows_a_large_raster_that_has_overviews() -> None:
    """The guard keys on the missing pyramid, not on the pixel count alone."""
    with TemporaryDirectory() as tmpdir:
        with rasterio.open(single_band_dataset) as src:
            profile = src.profile
            pixels = src.read()

        with_overviews = Path(tmpdir) / "with_overviews.tif"
        with rasterio.open(with_overviews, "w", **profile) as dst:
            dst.write(pixels)
            dst.build_overviews([2, 4], rasterio.enums.Resampling.average)

        out_jpeg = Path(tmpdir) / "export.jpg"
        with patch.object(raster_export, "MAX_PIXELS_WITHOUT_OVERVIEWS", 100):
            export_raster_to_jpeg(
                with_overviews, out_jpeg, test_stac_props_dsm, max_dimension=8
            )

        assert read_jpeg(out_jpeg)[2][1] == 8


def test_export_does_not_check_overviews_when_no_resizing_is_needed() -> None:
    """A raster already within the size cap is read whole, so the guard is moot."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"
        with patch.object(raster_export, "MAX_PIXELS_WITHOUT_OVERVIEWS", 100):
            export_raster_to_jpeg(
                single_band_dataset, out_jpeg, test_stac_props_dsm, max_dimension=4096
            )

        assert read_jpeg(out_jpeg)[2] == (203, 240)


def test_build_color_table_separates_a_flat_range_at_large_magnitudes() -> None:
    """The degenerate range guard scales with the value.

    A fixed epsilon is lost to floating point at large magnitudes: 1e10 + 1e-6
    rounds straight back to 1e10, leaving every entry on the same value.
    """
    color_table = build_color_table("viridis", 1e10, 1e10, steps=8)

    values = [
        float(line.split(" ")[0]) for line in color_table.strip().split("\n")[:-1]
    ]
    assert len(values) == len(set(values))


def test_export_applies_a_color_ramp_to_a_multiband_raster(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """Single band settings are honored even when the raster has several bands.

    The settings' shape picks the path, not the band count, so a color ramp saved
    against a raster whose band count later changed still exports.
    """
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            multiband_dataset,
            out_jpeg,
            multiband_stac_properties,
            symbology=create_single_band_symbology(colorRamp="viridis"),
        )

        driver, band_count, _, _ = read_jpeg(out_jpeg)
        # the color ramp turns the one band it reads into an RGB image
        assert driver == "JPEG"
        assert band_count == 3


def test_export_rejects_symbology_with_neither_shape() -> None:
    """Settings carrying no color ramp and no band composition are rejected."""
    with TemporaryDirectory() as tmpdir:
        with pytest.raises(SymbologyError, match="color ramp or a band composition"):
            export_raster_to_jpeg(
                single_band_dataset,
                Path(tmpdir) / "export.jpg",
                test_stac_props_dsm,
                symbology={"mode": "minMax", "opacity": 100},
            )


def test_export_uses_the_band_composition_when_there_is_no_color_ramp(
    multiband_stac_properties: Dict[str, Any],
) -> None:
    """Multiband settings still take the band composition path."""
    with TemporaryDirectory() as tmpdir:
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            multiband_dataset,
            out_jpeg,
            multiband_stac_properties,
            symbology=create_multiband_symbology(multiband_stac_properties),
        )

        assert read_jpeg(out_jpeg)[1] == 3


def create_two_band_raster(tmpdir: str) -> Tuple[Path, Dict[str, Any]]:
    """Writes a two band raster, a count neither export path is built around."""
    raster = Path(tmpdir) / "two_band.tif"

    with rasterio.open(multiband_dataset) as src:
        profile = src.profile
        pixels = src.read([1, 2])

    profile.update(count=2, photometric=None)
    with rasterio.open(raster, "w", **profile) as dst:
        dst.write(pixels)

    return raster, get_stac_properties(get_info(raster))


def test_export_converts_a_two_band_raster_without_symbology() -> None:
    """Two bands are too few for an RGB composition, so one band is used."""
    with TemporaryDirectory() as tmpdir:
        raster, stac_properties = create_two_band_raster(tmpdir)
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(raster, out_jpeg, stac_properties)

        assert read_jpeg(out_jpeg)[1] == 1


def test_export_applies_a_color_ramp_to_a_two_band_raster() -> None:
    """A color ramp works on a two band raster.

    Choosing the path by band count used to send anything past one band to the
    multiband export, where a two band raster could only ever fail.
    """
    with TemporaryDirectory() as tmpdir:
        raster, stac_properties = create_two_band_raster(tmpdir)
        out_jpeg = Path(tmpdir) / "export.jpg"

        export_raster_to_jpeg(
            raster,
            out_jpeg,
            stac_properties,
            symbology=create_single_band_symbology(colorRamp="viridis"),
        )

        assert read_jpeg(out_jpeg)[1] == 3

import subprocess
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.utils import ImageProcessor as image_processor
from app.utils.ImageProcessor import (
    ImageProcessor,
    build_cog_command,
    get_info,
    get_utm_epsg_from_latlon,
    get_wgs84_info,
    is_cog,
    resampling_for,
    run_gdal,
)

single_band_dataset = Path("/app/app/tests/data/test.tif")


def stage_input(
    tmp_path: Path,
    dataset: Path = single_band_dataset,
    to_wgs84: bool = False,
    as_cog: bool = False,
) -> Path:
    """Copies a dataset into an input directory laid out the way uploads are.

    ImageProcessor writes to the input's grandparent directory and removes the
    input's parent, so the dataset has to sit one level below the output dir.
    """
    in_dir = tmp_path / "input"
    in_dir.mkdir(parents=True, exist_ok=True)
    staged = in_dir / dataset.name

    source = dataset
    if to_wgs84:
        warped = tmp_path / f"wgs84_{dataset.name}"
        run_gdal(["gdalwarp", "-q", "-t_srs", "EPSG:4326", str(dataset), str(warped)])
        source = warped

    if as_cog:
        run_gdal(["gdal_translate", "-q", "-of", "COG", str(source), str(staged)])
    else:
        run_gdal(["gdal_translate", "-q", str(source), str(staged)])

    return staged


def write_raster_without_stats(
    path: Path, count: int = 1, crs: str | None = "EPSG:32616"
) -> Path:
    """Writes a small raster that has no precomputed statistics."""
    data = np.arange(count * 64 * 64, dtype="uint16").reshape(count, 64, 64)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=count,
        dtype="uint16",
        crs=crs,
        transform=from_origin(0, 64, 1, 1),
    ) as dst:
        dst.write(data)

    return path


def band_metadata(info: dict) -> dict:
    """Returns the default metadata domain for the first band."""
    return info["bands"][0].get("metadata", {}).get("", {})


def test_run_reprojects_a_wgs84_raster_to_utm(tmp_path: Path) -> None:
    in_raster = stage_input(tmp_path, to_wgs84=True)

    out_raster = ImageProcessor(str(in_raster), project_to_utm=True).run()

    with rasterio.open(out_raster) as src:
        assert src.crs.to_epsg() == 32616
    assert is_cog(get_info(out_raster, with_stats=False))


def test_run_reprojects_a_raster_that_is_already_a_cog(tmp_path: Path) -> None:
    in_raster = stage_input(tmp_path, to_wgs84=True, as_cog=True)
    assert is_cog(get_info(in_raster, with_stats=False))

    out_raster = ImageProcessor(str(in_raster), project_to_utm=True).run()

    with rasterio.open(out_raster) as src:
        assert src.crs.to_epsg() == 32616


def test_run_moves_a_cog_that_does_not_need_reprojecting(tmp_path: Path) -> None:
    in_raster = stage_input(tmp_path, as_cog=True)

    processor = ImageProcessor(str(in_raster), project_to_utm=True)
    out_raster = processor.run()

    assert out_raster == tmp_path / in_raster.name
    assert out_raster.exists()
    assert not in_raster.parent.exists()
    assert is_cog(get_info(out_raster, with_stats=False))
    assert processor.stac_properties["raster"][0]["stats"]["minimum"] is not None


def test_run_creates_a_preview_image(tmp_path: Path) -> None:
    in_raster = stage_input(tmp_path)

    processor = ImageProcessor(str(in_raster))
    processor.run()

    assert processor.preview_out_path.exists()


def test_convert_to_cog_sets_predictor(tmp_path: Path) -> None:
    in_raster = stage_input(tmp_path)

    out_raster = ImageProcessor(str(in_raster)).run()

    image_structure = get_info(out_raster, with_stats=False)["metadata"][
        "IMAGE_STRUCTURE"
    ]
    assert image_structure["LAYOUT"] == "COG"
    assert "PREDICTOR" in image_structure


def test_run_selects_resampling_from_band_count(tmp_path: Path) -> None:
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    in_raster = write_raster_without_stats(in_dir / "rgb.tif", count=3)

    processor = ImageProcessor(str(in_raster))
    processor.run()

    assert processor.resampling == "cubic"
    assert processor.preview_out_path.exists()


@pytest.mark.parametrize(
    "band_count,expected",
    [
        (0, "bilinear"),
        (1, "bilinear"),
        (2, "bilinear"),
        (3, "cubic"),
        (4, "cubic"),
        (80, "cubic"),
    ],
)
def test_resampling_for(band_count: int, expected: str) -> None:
    assert resampling_for(band_count) == expected


def test_build_cog_command_uses_the_requested_resampling() -> None:
    command = build_cog_command(
        Path("in.tif"), Path("out.tif"), resampling_for(3), "EPSG:32616"
    )

    assert "OVERVIEW_RESAMPLING=cubic" in command
    assert "WARP_RESAMPLING=cubic" in command
    assert "TARGET_SRS=EPSG:32616" in command
    # gdalwarp flags are not valid for gdal_translate
    assert "-t_srs" not in command
    assert "-s_srs" not in command


def test_build_cog_command_omits_warp_options_without_an_epsg_code() -> None:
    command = build_cog_command(Path("in.tif"), Path("out.tif"))

    assert not any(arg.startswith("TARGET_SRS") for arg in command)
    assert not any(arg.startswith("WARP_RESAMPLING") for arg in command)


def test_build_cog_command_always_requests_at_least_one_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(image_processor.multiprocessing, "cpu_count", lambda: 1)

    command = build_cog_command(Path("in.tif"), Path("out.tif"))

    assert "NUM_THREADS=1" in command


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (41.6, -93.6, "EPSG:32615"),
        (0.0, 0.0, "EPSG:32631"),
        (-33.9, 151.2, "EPSG:32756"),
        (10.0, 180.0, "EPSG:32660"),
        (10.0, -180.0, "EPSG:32601"),
    ],
)
def test_get_utm_epsg_from_latlon(lat: float, lon: float, expected: str) -> None:
    assert get_utm_epsg_from_latlon(lat, lon) == expected


def test_get_utm_epsg_from_latlon_rejects_out_of_range_values() -> None:
    with pytest.raises(ValueError):
        get_utm_epsg_from_latlon(91.0, 0.0)


def test_run_gdal_raises_with_the_gdal_error_message(tmp_path: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        run_gdal(["gdalinfo", str(tmp_path / "does_not_exist.tif")])

    assert exc_info.value.stderr
    assert "does_not_exist.tif" in exc_info.value.stderr


def test_get_info_without_stats_skips_statistics(tmp_path: Path) -> None:
    raster = write_raster_without_stats(tmp_path / "no_stats.tif")

    info = get_info(raster, with_stats=False)

    assert "STATISTICS_MINIMUM" not in band_metadata(info)
    assert not Path(f"{raster}.aux.xml").exists()


def test_get_info_computes_missing_statistics(tmp_path: Path) -> None:
    raster = write_raster_without_stats(tmp_path / "no_stats.tif")

    info = get_info(raster)

    assert "STATISTICS_MINIMUM" in band_metadata(info)


def test_get_wgs84_info_handles_a_raster_without_a_crs(tmp_path: Path) -> None:
    raster = write_raster_without_stats(tmp_path / "no_crs.tif", crs=None)

    assert get_wgs84_info(raster) == (False, None, None)

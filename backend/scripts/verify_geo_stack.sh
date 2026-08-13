#!/usr/bin/env bash
#
# Asserts that the geospatial stack in the running image provides everything the
# backend uses. Written to run unmodified in both the conda-based image and the
# uv-based one, so the two can be compared directly:
#
#   docker compose exec backend bash /app/scripts/verify_geo_stack.sh
#
# Pass --cli-only to skip the Python checks, for smoke-testing the geo-base image
# before any Python environment exists. Both mounts are needed: one supplies this
# script, the other the raster the gdal checks operate on.
#
#   docker run --rm \
#     -v "$PWD/backend/scripts:/scripts:ro" \
#     -v "$PWD/backend/app/tests/data:/app/app/tests/data:ro" \
#     gdslab/d2s-geo-base:<tag> bash /scripts/verify_geo_stack.sh --cli-only
#
# That checks /opt/geo, which is the tree the base image puts on PATH. The tree the
# application image actually receives is /opt/geo-runtime, stripped and pruned; to
# check that one, point PATH and GEO_PREFIX at it. See .github/workflows/geo-base.yml,
# which runs both.
#
# Several of the paths checked here have no pytest coverage: filters.csf,
# writers.gdal, the COG and JPEG conversions in ImageProcessor, and the pdal
# Python bindings. This script is where those regressions get caught.

set -euo pipefail

CLI_ONLY=false
case "${1:-}" in
    --cli-only) CLI_ONLY=true ;;
    "") ;;
    # Silently ignoring an unrecognised flag would run the full suite while the
    # caller believed they had asked for something narrower.
    *) printf '  FAIL  unknown argument: %s (only --cli-only is accepted)\n' "$1" >&2
       exit 1 ;;
esac

# Which tree to inspect. The geo base ships two: /opt/geo, unstripped and carrying
# headers for the application's build stage, and /opt/geo-runtime, the stripped and
# pruned copy that is what actually reaches the application image. Overriding this
# alongside PATH is how the runtime tree gets checked; on its own PATH would move
# the CLI checks but leave the linkage sweep reading the wrong tree.
GEO_PREFIX="${GEO_PREFIX:-/opt/geo}"

# The geo base records what it was built from. Reading it means the Python
# version assertions below compare the pinned bindings against the libraries
# actually present, rather than against numbers copied into this script. The
# fallbacks cover the conda image, which has no such manifest.
if [[ -r "$GEO_PREFIX/VERSIONS" ]]; then
    # shellcheck disable=SC1091
    . "$GEO_PREFIX/VERSIONS"
fi

GDAL_EXPECTED="${GDAL_EXPECTED:-${GDAL:-3.12.3}}"
PDAL_EXPECTED="${PDAL_EXPECTED:-${PDAL:-2.10.0}}"
GEOS_EXPECTED="${GEOS_EXPECTED:-${GEOS:-3.14.1}}"
PROJ_EXPECTED="${PROJ_EXPECTED:-${PROJ:-9.7}}"

# Not a bare mktemp -d: that lands in /tmp, and the production backend runs with a
# read-only root filesystem and a tmpfs on /var/tmp only, so the documented command
# would die here before running a single check -- on the one image where verifying
# the shipped stack matters most. /var/tmp is writable in the dev and geo base
# images too, so this works everywhere the script is meant to run.
WORK="$(mktemp -d -p "${TMPDIR:-/var/tmp}")"
trap 'rm -rf "$WORK"' EXIT

pass() { printf '  ok    %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1" >&2; exit 1; }
section() { printf '\n== %s\n' "$1"; }

# Locate the raster the CLI checks operate on. /app is the image layout; the
# repo-relative path covers running this from a checkout. A missing fixture is a
# failure rather than a skip: the application image ships it and CI mounts it, so
# its absence means the checks below are not running where someone thinks they are.
TEST_TIF=""
for candidate in /app/app/tests/data/test.tif ./app/tests/data/test.tif; do
    [[ -f "$candidate" ]] && TEST_TIF="$candidate" && break
done
[[ -n "$TEST_TIF" ]] || {
    printf '  FAIL  test.tif not found; mount app/tests/data to run the gdal checks\n' >&2
    exit 1
}

section "versions"
gdalinfo --version | grep -qF "GDAL $GDAL_EXPECTED" \
    || fail "gdalinfo reports $(gdalinfo --version), expected GDAL $GDAL_EXPECTED"
pass "gdal $GDAL_EXPECTED"
pdal --version | grep -qF "$PDAL_EXPECTED" \
    || fail "pdal reports $(pdal --version | tr -d '\n'), expected $PDAL_EXPECTED"
pass "pdal $PDAL_EXPECTED"

# Both loops anchor on the short-name column -- "  <name> -raster-" / "  <name>
# -vector-" -- rather than searching the line. The descriptions repeat driver names,
# so a loose match reports a driver present when only a relative of it is: GeoJSON
# matches GeoJSONSeq's "GeoJSON Sequence", and JPEG matches JP2OpenJPEG's "JPEG
# 2000". Word boundaries do not help, since both are standalone words there.
section "gdal raster drivers"
formats="$(gdalinfo --formats)"
for driver in GTiff COG VRT MEM JPEG PNG JP2OpenJPEG; do
    grep -q "^ *${driver} -" <<<"$formats" || fail "raster driver missing: $driver"
    pass "$driver"
done

section "ogr vector drivers"
vformats="$(ogrinfo --formats)"
for driver in "ESRI Shapefile" FlatGeobuf GPKG GeoJSON SQLite CSV; do
    grep -q "^ *${driver} -" <<<"$vformats" || fail "vector driver missing: $driver"
    pass "$driver"
done

section "pdal stages"
drivers="$(pdal --drivers)"
for stage in readers.las readers.copc writers.las writers.copc writers.gdal \
             filters.assign filters.csf filters.range filters.hag_dem \
             filters.decimation filters.hexbin filters.stats filters.info; do
    grep -qw "$stage" <<<"$drivers" || fail "pdal stage missing: $stage"
    pass "$stage"
done

section "geospatial cli tools on PATH"
for tool in gdalinfo gdal_translate gdaldem ogrinfo pdal untwine; do
    command -v "$tool" >/dev/null || fail "not on PATH: $tool"
    pass "$tool"
done

section "gdal cli paths used by ImageProcessor and the hillshade tool"
gdal_translate -q -of COG -co COMPRESS=DEFLATE -co BIGTIFF=YES \
    -co STATISTICS=YES "$TEST_TIF" "$WORK/cog.tif"
# A COG reads back through the GTiff driver; the tell is the layout metadata.
# Read it from the plain text report rather than the json one, so this section
# also runs in the geo base image, which ships no Python. Fed by herestring rather
# than a pipe because grep -q closes the read end at the first match: with pipefail
# set, a report long enough to outlive the pipe buffer would leave gdalinfo on
# SIGPIPE and fail an assertion that had already passed.
grep -q 'LAYOUT=COG' <<<"$(gdalinfo "$WORK/cog.tif")" \
    || fail "COG output does not report LAYOUT=COG"
pass "gdal_translate -of COG"
gdalinfo -json -stats "$WORK/cog.tif" >/dev/null
pass "gdalinfo -json -stats"
gdal_translate -q -of JPEG -ot Byte -co QUALITY=75 -outsize 320 0 \
    "$TEST_TIF" "$WORK/preview.jpg"
test -s "$WORK/preview.jpg" || fail "JPEG preview is empty"
pass "gdal_translate -of JPEG"
gdaldem hillshade -q -z 1 -compute_edges -multidirectional -of GTIFF \
    "$TEST_TIF" "$WORK/hillshade.tif"
test -s "$WORK/hillshade.tif" || fail "hillshade output is empty"
pass "gdaldem hillshade"

# Ahead of the --cli-only exit on purpose: an unresolved libgomp or libcurl shows
# up first in the geo base image, and a bad strip or an over-broad prune in the
# runtime tree shows up nowhere else at all. The venv branch is skipped when there
# is no Python environment yet, which is why this can run in both images.
#
# Scoped to the stack this image builds. A conda environment is not checked here:
# it ships optional GPU and arrow-flight libraries that are never loaded and
# always report as missing, which says nothing about the geospatial stack.
section "shared library resolution"
geo_objects="$(
    for dir in "$GEO_PREFIX/lib" "$GEO_PREFIX/bin"; do
        [[ -d "$dir" ]] && find "$dir" -type f
    done 2>/dev/null || true
)"
venv_objects="$([[ -d /opt/venv ]] && find /opt/venv -name '*.so*' -type f 2>/dev/null || true)"
# Both directories are optional, so a wrong GEO_PREFIX would sweep nothing and report
# success. Counting the two separately keeps that visible: in the application image
# the venv contributes most of the objects, so a single total would stay large and
# healthy-looking even with the geo tree missing entirely.
[[ -n "$geo_objects" ]] || fail "no objects under $GEO_PREFIX; GEO_PREFIX is wrong"
objects="$(printf '%s\n' "$geo_objects" "$venv_objects" | grep -v '^$' || true)"
missing="$(xargs -r -n 50 ldd <<<"$objects" 2>/dev/null | grep 'not found' || true)"
[[ -z "$missing" ]] || fail "unresolved shared libraries:
$missing"
pass "no unresolved shared libraries in $(grep -c . <<<"$geo_objects") objects under \
$GEO_PREFIX and $([[ -n "$venv_objects" ]] && grep -c . <<<"$venv_objects" || echo 0) under /opt/venv"

if [[ "$CLI_ONLY" == true ]]; then
    printf '\nCLI CHECKS PASSED\n'
    exit 0
fi

section "python imports and native versions"
GDAL_EXPECTED="$GDAL_EXPECTED" GEOS_EXPECTED="$GEOS_EXPECTED" \
PROJ_EXPECTED="$PROJ_EXPECTED" PDAL_EXPECTED="$PDAL_EXPECTED" python - <<'PY'
import os

from osgeo import gdal, ogr, osr  # noqa: F401
import fiona
import geopandas  # noqa: F401
import laspy
import numpy
import openpyxl  # noqa: F401
import pandas
import pdal
import pyarrow  # noqa: F401
import pyogrio  # noqa: F401
import pyproj
import rasterio
import rasterstats  # noqa: F401
import shapely
from fiona.io import ZipMemoryFile  # noqa: F401
from rasterio.fill import fillnodata  # noqa: F401
from rasterio.warp import transform_bounds  # noqa: F401

gdal_expected = os.environ["GDAL_EXPECTED"]
geos_expected = tuple(int(p) for p in os.environ["GEOS_EXPECTED"].split("."))
proj_expected = os.environ["PROJ_EXPECTED"]
pdal_expected = os.environ["PDAL_EXPECTED"]

assert gdal.__version__ == gdal_expected, f"osgeo.gdal {gdal.__version__}"
assert rasterio.__gdal_version__ == gdal_expected, f"rasterio {rasterio.__gdal_version__}"
assert shapely.geos_version == geos_expected, f"shapely geos {shapely.geos_version}"
assert pyproj.proj_version_str.startswith(proj_expected), pyproj.proj_version_str
assert laspy.LazBackend.Lazrs.is_available(), "laspy lazrs backend unavailable"
# The bindings carry their own version (3.x) but report the libpdal they linked,
# which is the number that has to match this image.
assert pdal.info.version == pdal_expected, f"pdal bindings linked {pdal.info.version}"

print(f"  ok    osgeo.gdal {gdal.__version__}")
print(f"  ok    rasterio {rasterio.__version__} on GDAL {rasterio.__gdal_version__}")
print(f"  ok    fiona {fiona.__version__} on GDAL {fiona.__gdal_version__}")
print(f"  ok    shapely {shapely.__version__} on GEOS {'.'.join(map(str, shapely.geos_version))}")
print(f"  ok    pyproj {pyproj.__version__} on PROJ {pyproj.proj_version_str}")
print(f"  ok    pdal {pdal.__version__} on libpdal {pdal.info.version}")
print(f"  ok    laspy {laspy.__version__} with lazrs")
print(f"  ok    numpy {numpy.__version__}, pandas {pandas.__version__}")
PY

section "untwine las to copc"
python - "$WORK" <<'PY'
import sys

import laspy
import numpy as np

work = sys.argv[1]
header = laspy.LasHeader(point_format=3, version="1.2")
header.offsets = [0.0, 0.0, 0.0]
header.scales = [0.01, 0.01, 0.01]
las = laspy.LasData(header)
rng = np.random.default_rng(0)
las.x = rng.uniform(0, 100, 2000)
las.y = rng.uniform(0, 100, 2000)
las.z = rng.uniform(0, 30, 2000)
las.write(f"{work}/points.las")
PY
untwine -i "$WORK/points.las" -o "$WORK/points.copc.laz" --a_srs EPSG:32616 >/dev/null
test -s "$WORK/points.copc.laz" || fail "untwine produced no output"
pdal info --summary "$WORK/points.copc.laz" >/dev/null
pass "untwine produced a readable copc"
python -c "
import laspy, sys
with laspy.open(sys.argv[1]) as f:
    assert f.header.point_count == 2000, f.header.point_count
" "$WORK/points.copc.laz"
pass "copc round-trips through laspy with all points"

section "pdal pipeline with csf and writers.gdal"
cat > "$WORK/csf.json" <<PIPELINE
[
    "$WORK/points.las",
    {"type": "filters.csf"},
    {
        "type": "writers.gdal",
        "filename": "$WORK/csf_dem.tif",
        "gdaldriver": "GTiff",
        "output_type": "min",
        "resolution": 5.0
    }
]
PIPELINE
pdal pipeline "$WORK/csf.json"
gdalinfo "$WORK/csf_dem.tif" >/dev/null || fail "writers.gdal output unreadable"
pass "filters.csf into writers.gdal"

section "pdal python bindings"
python - "$WORK" <<'PY'
import sys

import pdal

work = sys.argv[1]
copc = f"{work}/points.copc.laz"

# mirrors app/api/extras.py
pipeline = pdal.Reader.copc(copc) | pdal.Filter.decimation(step=2)
count = pipeline.execute()
assert count > 0, count
assert len(pipeline.arrays[0]["Z"]) > 0

# mirrors app/utils/stac/pdal_to_stac.py
stats = (
    pdal.Reader.copc(copc)
    | pdal.Filter.hexbin()
    | pdal.Filter.stats()
    | pdal.Filter.info()
)
stats.execute()
assert stats.metadata, "pipeline produced no metadata"
print(f"  ok    decimation read {count} points")
print("  ok    hexbin/stats/info metadata")
PY

section "geopandas and pandas io"
python - "$WORK" <<'PY'
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

work = sys.argv[1]
# inside UTM zone 16N, so the reprojection below stays finite
gdf = gpd.GeoDataFrame({"a": [1]}, geometry=[Point(-86.9, 40.4)], crs="EPSG:4326")
gdf = gdf.to_crs("EPSG:32616")
gdf.to_file(f"{work}/x.shp", driver="ESRI Shapefile")
gdf.to_file(f"{work}/x.fgb", driver="FlatGeobuf")
gdf.to_parquet(f"{work}/x.parquet", compression="snappy")
assert len(gpd.read_file(f"{work}/x.fgb")) == 1
assert len(gpd.read_file(f"{work}/x.shp")) == 1

frame = pd.DataFrame({"a": [1]})
frame.to_excel(f"{work}/x.xlsx", index=False)
assert len(pd.read_excel(f"{work}/x.xlsx")) == 1
print("  ok    shapefile, flatgeobuf, geoparquet, xlsx")
PY

section "application entry points"
for tool in python alembic celery uvicorn rsync curl; do
    command -v "$tool" >/dev/null || fail "not on PATH: $tool"
    pass "$tool"
done

printf '\nALL CHECKS PASSED\n'

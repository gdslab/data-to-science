#!/bin/sh
#
# Asserts that the geospatial declarations in pyproject.toml describe the libraries a
# geo base image actually provides.
#
#   check_geo_pins.sh <VERSIONS-file> <pyproject.toml>
#
# Two callers, one copy. backend.dockerfile runs it against the image it is about to
# compile bindings against; .github/workflows/geo-base.yml runs it against the image it
# is about to publish. Those are the two directions the coupling can break:
#
#   - a pin moves without the image  -- caught at application build time
#   - the image moves without a pin  -- caught in CI, before a mutable tag is published
#     and every later backend build starts failing
#
# Keeping the comparison in one file is the point. Two copies of it would drift, and the
# drift would stay invisible until a build broke somewhere unrelated to the change.
#
# POSIX sh, not bash: the application build stage runs this under Ubuntu's /bin/sh.

set -eu

versions="${1:-}"
pyproject="${2:-}"

if [ -z "$versions" ] || [ -z "$pyproject" ]; then
    echo "usage: check_geo_pins.sh <VERSIONS-file> <pyproject.toml>" >&2
    exit 1
fi

# POSIX `.` searches $PATH when its operand contains no slash, so a caller passing a bare
# filename would source whatever $PATH turned up first rather than the file they named.
# Both callers pass absolute paths today; this keeps that from being load-bearing.
case "$versions" in
    */*) ;;
    *) versions="./$versions" ;;
esac

# An unreadable input is a failure, not a skip. Silently passing because a path was
# wrong is the failure mode this check exists to prevent in the first place.
[ -r "$versions" ] || { echo "check-geo-pins: cannot read $versions" >&2; exit 1; }
[ -r "$pyproject" ] || { echo "check-geo-pins: cannot read $pyproject" >&2; exit 1; }

# shellcheck disable=SC1090
. "$versions"

# gdal== is the library version. pdal== is the bindings version and tracks its own
# release series, so the libpdal it links is declared in a trailing comment instead.
pinned_gdal="$(sed -n 's/.*"gdal==\([0-9][^"]*\)".*/\1/p' "$pyproject")"
pinned_pdal="$(sed -n 's/.*"pdal==[^"]*".*# libpdal: *\([0-9][0-9.]*\).*/\1/p' "$pyproject")"

# Both are reported before either exits, because a version bump usually moves both and
# failing on the first would hide the second. A declaration that cannot be parsed
# compares unequal and fails as <unparsed>, so deleting one breaks the build rather
# than turning its own check off.
agree=true
if [ "$pinned_gdal" != "${GDAL:-}" ]; then
    echo "geo base provides GDAL ${GDAL:-<absent from VERSIONS>} but pyproject.toml pins gdal==${pinned_gdal:-<unparsed>}." >&2
    agree=false
fi
if [ "$pinned_pdal" != "${PDAL:-}" ]; then
    echo "geo base provides libpdal ${PDAL:-<absent from VERSIONS>} but pyproject.toml declares libpdal ${pinned_pdal:-<unparsed>}." >&2
    agree=false
fi

if [ "$agree" != true ]; then
    echo "Rebuild gdslab/d2s-geo-base or change the declarations so the two agree." >&2
    exit 1
fi

echo "  ok    gdal==${pinned_gdal} and libpdal ${pinned_pdal} match ${versions}"

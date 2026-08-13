# Native geospatial stack for the d2s backend.
#
# Published as gdslab/d2s-geo-base:latest and consumed by backend.dockerfile.
# Building it here keeps GDAL/PDAL/Untwine compilation out of the application
# image build, which otherwise takes 20-35 minutes per run.
#
# Coupling rule: the versions below and the gdal==/pdal== pins in pyproject.toml
# describe the same libraries, because the Python bindings are compiled against
# them. Changing one means changing the other and republishing this image in the
# same pull request. Since the tag is mutable, pull it before building the
# application image rather than trusting a local copy, and run
# scripts/verify_geo_stack.sh, which fails when the CLI tools and the Python
# bindings disagree about a version.
#
#   docker build -f backend/geobase.dockerfile -t gdslab/d2s-geo-base:latest backend/

# Declared once here, before the first FROM, and inherited by each stage with a
# bare re-declaration. Keeping a single copy stops the OCI labels below from
# drifting away from what was actually built.
#
# Each source is pinned by sha256. Bump a version and its hash together; get the
# new hash from the upstream release, or from `sha256sum` over a download you
# have checked against whatever checksum upstream publishes.
ARG PROJ_VERSION=9.7.1
ARG PROJ_SHA256=6c097dc803c561929cdfcc46e4bf9945ea977611fb31493ad14e88edaeae260f
ARG GEOS_VERSION=3.14.1
ARG GEOS_SHA256=3c20919cda9a505db07b5216baa980bacdaa0702da715b43f176fb07eff7e716
ARG GEOTIFF_VERSION=1.7.4
ARG GEOTIFF_SHA256=c598d04fdf2ba25c4352844dafa81dde3f7fd968daa7ad131228cd91e9d3dc47
ARG GDAL_VERSION=3.12.3
ARG GDAL_SHA256=1fdfe51181d08b9b83037b611da4de4a7cf1fca69e6564945ac99d3f7d0367dd
ARG PDAL_VERSION=2.10.0
ARG PDAL_SHA256=65eba26e24a2cb1752d3542cc84e8035ecb8dc890b72145128f9b33bd184f2f5
ARG UNTWINE_VERSION=1.5.0
ARG UNTWINE_SHA256=8fa431bb5ce60eccf83c56bfbdb3e51118d70b56eff5e2671384f6887e8c9a6c

FROM ubuntu:24.04 AS build

ARG PROJ_VERSION
ARG PROJ_SHA256
ARG GEOS_VERSION
ARG GEOS_SHA256
ARG GEOTIFF_VERSION
ARG GEOTIFF_SHA256
ARG GDAL_VERSION
ARG GDAL_SHA256
ARG PDAL_VERSION
ARG PDAL_SHA256
ARG UNTWINE_VERSION
ARG UNTWINE_SHA256

# Dependencies are taken from apt only where they do not carry their own PROJ.
# libgeotiff-dev, libproj-dev and libgeos-dev are deliberately absent: noble ships
# PROJ 9.4, and linking against it would put two PROJ versions in the image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    curl \
    ca-certificates \
    sqlite3 \
    libsqlite3-dev \
    libtiff-dev \
    libjpeg-dev \
    libpng-dev \
    libopenjp2-7-dev \
    libdeflate-dev \
    libzstd-dev \
    liblzma-dev \
    zlib1g-dev \
    libcurl4-openssl-dev \
    libexpat1-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/fetch-source.sh /usr/local/bin/fetch-source
RUN chmod +x /usr/local/bin/fetch-source

WORKDIR /src

# PROJ
RUN fetch-source proj.tar.gz "${PROJ_SHA256}" \
        "https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz" \
    && tar -xzf proj.tar.gz \
    && cmake -S "proj-${PROJ_VERSION}" -B proj-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
        -DBUILD_TESTING=OFF \
        -DENABLE_CURL=ON \
        -DENABLE_TIFF=ON \
    && cmake --build proj-build --target install \
    && rm -rf proj.tar.gz "proj-${PROJ_VERSION}" proj-build

# GEOS
RUN fetch-source geos.tar.bz2 "${GEOS_SHA256}" \
        "https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2" \
    && tar -xjf geos.tar.bz2 \
    && cmake -S "geos-${GEOS_VERSION}" -B geos-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
        -DBUILD_TESTING=OFF \
    && cmake --build geos-build --target install \
    && rm -rf geos.tar.bz2 "geos-${GEOS_VERSION}" geos-build

# GDAL. GDAL_USE_EXTERNAL_LIBS=OFF turns every optional dependency off, then each
# GDAL_USE_<lib> below turns back on exactly what the application needs, so the
# dependency set does not drift with whatever apt happens to have installed.
# The driver set covers every format the backend reads or writes; COG lives inside
# the GTiff driver, and VRT/MEM/Memory are always built (no flag exists for them).
# GEOTIFF_INTERNAL is required: the apt libgeotiff links noble's PROJ 9.4.
# DXF is the one driver here the application never uses. It installs header.dxf,
# which pyogrio probes to locate the GDAL data directory; without it every import
# of geopandas warns that GDAL_DATA is unset even when it is correct.
RUN fetch-source gdal.tar.gz "${GDAL_SHA256}" \
        "https://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz" \
        "https://github.com/OSGeo/gdal/releases/download/v${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz" \
    && tar -xzf gdal.tar.gz \
    && cmake -S "gdal-${GDAL_VERSION}" -B gdal-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_PREFIX_PATH=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
        -DBUILD_SHARED_LIBS=ON \
        -DBUILD_APPS=ON \
        -DBUILD_TESTING=OFF \
        -DBUILD_PYTHON_BINDINGS=OFF \
        -DBUILD_JAVA_BINDINGS=OFF \
        -DBUILD_CSHARP_BINDINGS=OFF \
        -DGDAL_USE_EXTERNAL_LIBS=OFF \
        -DGDAL_USE_TIFF=ON \
        -DGDAL_USE_GEOTIFF_INTERNAL=ON \
        -DGDAL_USE_JPEG=ON \
        -DGDAL_USE_PNG=ON \
        -DGDAL_USE_OPENJPEG=ON \
        -DGDAL_USE_GEOS=ON \
        -DGDAL_USE_CURL=ON \
        -DGDAL_USE_SQLITE3=ON \
        -DGDAL_USE_EXPAT=ON \
        -DGDAL_USE_LIBXML2=ON \
        -DGDAL_USE_DEFLATE=ON \
        -DGDAL_USE_ZSTD=ON \
        -DGDAL_USE_ZLIB=ON \
        -DGDAL_USE_LIBLZMA=ON \
        -DGDAL_USE_JSONC_INTERNAL=ON \
        -DGDAL_USE_LERC_INTERNAL=ON \
        -DGDAL_BUILD_OPTIONAL_DRIVERS=OFF \
        -DOGR_BUILD_OPTIONAL_DRIVERS=OFF \
        -DGDAL_ENABLE_DRIVER_GTIFF=ON \
        -DGDAL_ENABLE_DRIVER_JPEG=ON \
        -DGDAL_ENABLE_DRIVER_PNG=ON \
        -DGDAL_ENABLE_DRIVER_JP2OPENJPEG=ON \
        -DOGR_ENABLE_DRIVER_SHAPE=ON \
        -DOGR_ENABLE_DRIVER_GEOJSON=ON \
        -DOGR_ENABLE_DRIVER_FLATGEOBUF=ON \
        -DOGR_ENABLE_DRIVER_GPKG=ON \
        -DOGR_ENABLE_DRIVER_SQLITE=ON \
        -DOGR_ENABLE_DRIVER_CSV=ON \
        -DOGR_ENABLE_DRIVER_DXF=ON \
    && cmake --build gdal-build --target install \
    && rm -rf gdal.tar.gz "gdal-${GDAL_VERSION}" gdal-build

# libgeotiff, required by PDAL (GDAL above uses its own internal copy, which is
# also how conda-forge builds this stack). Built from source rather than apt so it
# links the PROJ in /opt/geo instead of noble's PROJ 9.4.
RUN fetch-source geotiff.tar.gz "${GEOTIFF_SHA256}" \
        "https://download.osgeo.org/geotiff/libgeotiff/libgeotiff-${GEOTIFF_VERSION}.tar.gz" \
        "https://github.com/OSGeo/libgeotiff/releases/download/${GEOTIFF_VERSION}/libgeotiff-${GEOTIFF_VERSION}.tar.gz" \
    && tar -xzf geotiff.tar.gz \
    && cmake -S "libgeotiff-${GEOTIFF_VERSION}" -B geotiff-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_PREFIX_PATH=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
        -DWITH_UTILITIES=OFF \
    && cmake --build geotiff-build --target install \
    && rm -rf geotiff.tar.gz "libgeotiff-${GEOTIFF_VERSION}" geotiff-build

# PDAL. Only the CSF plugin is enabled; every other plugin defaults to off and
# none of them are reachable from the application. filters.hag_dem, readers/writers
# for las and copc, and writers.gdal are core stages.
RUN fetch-source pdal.tar.bz2 "${PDAL_SHA256}" \
        "https://github.com/PDAL/PDAL/releases/download/${PDAL_VERSION}/PDAL-${PDAL_VERSION}-src.tar.bz2" \
    && tar -xjf pdal.tar.bz2 \
    && cmake -S "PDAL-${PDAL_VERSION}-src" -B pdal-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_PREFIX_PATH=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
        -DWITH_TESTS=OFF \
        -DBUILD_PLUGIN_CSF=ON \
    && cmake --build pdal-build --target install \
    && rm -rf pdal.tar.bz2 "PDAL-${PDAL_VERSION}-src" pdal-build

# Untwine links libpdalcpp, so it has to come after PDAL.
RUN fetch-source untwine.tar.gz "${UNTWINE_SHA256}" \
        "https://github.com/hobuinc/untwine/releases/download/${UNTWINE_VERSION}/Untwine-${UNTWINE_VERSION}-src.tar.gz" \
    && tar -xzf untwine.tar.gz \
    && cmake -S "Untwine-${UNTWINE_VERSION}-src" -B untwine-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/geo \
        -DCMAKE_PREFIX_PATH=/opt/geo \
        -DCMAKE_INSTALL_RPATH=/opt/geo/lib \
    && cmake --build untwine-build --target install \
    && rm -rf untwine.tar.gz "Untwine-${UNTWINE_VERSION}-src" untwine-build

# Records what this image actually contains. backend.dockerfile compares this
# against its pinned bindings so a mismatch fails the build with both versions
# named, and verify_geo_stack.sh reads it instead of hardcoding expectations.
RUN printf 'GDAL=%s\nPDAL=%s\nPROJ=%s\nGEOS=%s\nGEOTIFF=%s\nUNTWINE=%s\n' \
        "${GDAL_VERSION}" "${PDAL_VERSION}" "${PROJ_VERSION}" \
        "${GEOS_VERSION}" "${GEOTIFF_VERSION}" "${UNTWINE_VERSION}" \
    > /opt/geo/VERSIONS

# /opt/geo keeps its headers and cmake config for the application's build stage.
# /opt/geo-runtime is the stripped copy the application's final stage consumes.
RUN cp -a /opt/geo /opt/geo-runtime \
    && rm -rf /opt/geo-runtime/include \
        /opt/geo-runtime/lib/cmake \
        /opt/geo-runtime/lib/pkgconfig \
        /opt/geo-runtime/share/man \
        /opt/geo-runtime/share/doc \
        /opt/geo-runtime/share/bash-completion \
    && find /opt/geo-runtime -name '*.a' -delete \
    && find /opt/geo-runtime/lib -name '*.so*' -type f \
        -exec strip --strip-unneeded {} + \
    && find /opt/geo-runtime/bin -type f \
        -exec sh -c 'strip --strip-unneeded "$1" 2>/dev/null || true' _ {} \;

FROM ubuntu:24.04

ARG GDAL_VERSION
ARG PDAL_VERSION
ARG PROJ_VERSION
ARG GEOS_VERSION
ARG GEOTIFF_VERSION
ARG UNTWINE_VERSION

LABEL org.opencontainers.image.title="d2s-geo-base" \
      org.opencontainers.image.description="GDAL, PDAL and Untwine built from source for the d2s backend" \
      org.opencontainers.image.source="https://github.com/hancocb/data-to-science" \
      io.d2s.gdal.version="${GDAL_VERSION}" \
      io.d2s.pdal.version="${PDAL_VERSION}" \
      io.d2s.proj.version="${PROJ_VERSION}" \
      io.d2s.geos.version="${GEOS_VERSION}" \
      io.d2s.geotiff.version="${GEOTIFF_VERSION}" \
      io.d2s.untwine.version="${UNTWINE_VERSION}"

# Runtime libraries only, so the CLI tools work when this image is run directly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libtiff6 \
    libjpeg-turbo8 \
    libpng16-16t64 \
    libopenjp2-7 \
    libdeflate0 \
    libzstd1 \
    liblzma5 \
    zlib1g \
    libsqlite3-0 \
    libexpat1 \
    libxml2 \
    libcurl4t64 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/geo /opt/geo
COPY --from=build /opt/geo-runtime /opt/geo-runtime

ENV PATH="/opt/geo/bin:${PATH}" \
    LD_LIBRARY_PATH=/opt/geo/lib \
    GDAL_DATA=/opt/geo/share/gdal \
    PROJ_LIB=/opt/geo/share/proj \
    PROJ_DATA=/opt/geo/share/proj \
    PDAL_DRIVER_PATH=/opt/geo/lib

CMD ["gdalinfo", "--version"]

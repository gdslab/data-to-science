"""Shared constants for data product types and job names.

This module provides centralized definitions to ensure consistency
across CRUD operations and avoid code duplication.
"""

# Data type classifications for data products
NON_RASTER_TYPES = frozenset({"panoramic", "point_cloud", "3dgs"})

# Job names used for filtering processing jobs
PROCESSING_JOB_NAMES = frozenset({
    "upload-data-product",
    "exg",
    "exg-process",
    "ndvi",
    "ndvi-process",
    "vari",
    "chm",
    "hillshade",
    "dtm",
})

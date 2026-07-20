"""Shared constants for data product types and job names.

This module provides centralized definitions to ensure consistency
across CRUD operations and avoid code duplication.
"""

# Data type classifications for data products
NON_RASTER_TYPES = frozenset({"panoramic", "point_cloud", "3dgs"})

# Data product types that cannot have XML metadata attached
XML_METADATA_EXCLUDED_TYPES = frozenset({"panoramic", "3dgs"})

# Vector layer property keys reserved for internal use. Uploaded feature
# properties with these names are dropped so they cannot shadow the real
# table columns when ST_AsMVT flattens the properties JSONB into map tiles
# (e.g., a re-uploaded D2S export carrying a stale feature_id).
RESERVED_VECTOR_PROPERTY_KEYS = frozenset({
    "id",
    "feature_id",
    "layer_name",
    "layer_id",
    "is_active",
    "project_id",
    "flight_id",
    "data_product_id",
})

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

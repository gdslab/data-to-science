"""STAC (SpatioTemporal Asset Catalog) utilities.

This package provides utilities for generating and managing STAC metadata
for geospatial data products.
"""

# Import lightweight classes that don't have circular dependencies
from .CachedSTACMetadata import CachedSTACMetadata
from .STACProperties import (
    STACEOProperties,
    STACProperties,
    STACPropertiesValidator,
    STACRasterProperties,
)

# Heavy dependencies - import directly to avoid circular imports:
# - from app.utils.stac.STACGenerator import STACGenerator
# - from app.utils.stac.STACCollectionManager import STACCollectionManager
#
# Custom exceptions - import directly to avoid circular imports:
# - from app.utils.stac.STACCollectionManager import (
#     STACAPIError, STACConnectionError, STACPublishError, STACConfigurationError
# )

__all__ = [
    "CachedSTACMetadata",
    "STACProperties",
    "STACPropertiesValidator",
    "STACRasterProperties",
    "STACEOProperties",
]

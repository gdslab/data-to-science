import json
from typing import TypedDict

from fastapi.encoders import jsonable_encoder
from geojson_pydantic import FeatureCollection

from app.schemas.data_product_metadata import ZonalStatistics
from app.tasks import generate_zonal_statistics


def get_zonal_statistics(in_raster: str, bbox_feature: str) -> list[ZonalStatistics]:
    """Returns zonal statistics for polygon overlaying a single-band raster.

    Args:
        in_raster (str): Path to single-band raster.
        bbox_feature (str): GeoJSON Feature for polygon.

    Returns:
        list[ZonalStats]: List of zonal statistic dictionaries for each zone.
    """
    bbox_json_string = json.dumps(jsonable_encoder(bbox_feature.__dict__))
    stats = generate_zonal_statistics(in_raster, bbox_json_string)

    return stats

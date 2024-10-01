import os
from typing import List

import geopandas as gpd
import numpy as np
from geojson_pydantic import Feature
from shapely.geometry import MultiLineString, MultiPolygon, MultiPoint
from staticmap import CircleMarker, Line, Polygon, StaticMap

from app.core.config import settings


class MapMaker:
    """Used to create static map previews for display on frontend application."""

    def __init__(self, features: list[Feature], outpath: str):
        self.features = features
        self.outpath = outpath
        self.preview_img = ""

        mapbox_access_token = os.environ.get("MAPBOX_ACCESS_TOKEN")

        size = (128, 128)
        padding = (16, 16)
        if mapbox_access_token:
            basemap = (
                "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token="
                + mapbox_access_token
            )
        else:
            basemap = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"

        headers = {"User-Agent": "StaticMap", "Referer": settings.API_DOMAIN}

        self.map = StaticMap(
            width=size[0],
            height=size[1],
            padding_x=padding[0],
            padding_y=padding[1],
            url_template=basemap,
            headers=headers,
        )

        # Standardize geometry type for features
        simplified_features_gdf: gpd.GeoDataFrame = simplify_geometry(
            gpd.GeoDataFrame.from_features(self.features, crs="EPSG:4326")
        )

        # Get list of Features from Geopandas DataFrame
        simplified_features: List[Feature] = [
            Feature(**feature)
            for feature in simplified_features_gdf.to_geo_dict()["features"]
        ]

        # Iterate over each feature and add to map
        for feature in simplified_features:
            if feature and hasattr(feature, "geometry") and feature.geometry:
                geom_type = feature.geometry.type.lower()
                if geom_type == "point" or geom_type == "multipoint":
                    self.map.add_marker(create_point(feature.geometry.coordinates))
                elif geom_type == "linestring" or geom_type == "multilinestring":
                    self.map.add_line(create_line(feature.geometry.coordinates))
                elif geom_type == "polygon" or geom_type == "multipolygon":
                    self.map.add_polygon(
                        create_polygon(feature.geometry.coordinates[0])
                    )
                else:
                    raise ValueError(f"Unknown geometry type: {geom_type}")

    def save(self, outname: str = "preview_map.png") -> None:
        image = self.map.render()
        image.save(os.path.join(self.outpath, outname))
        self.preview_img = os.path.join(self.outpath, outname)


def create_polygon(coords: List[List[float]]) -> Polygon:
    fill_color = "#fcd34d66"  # 40% opacity
    outline_color = "#fcd34d"
    simplify = False
    return Polygon(
        coords=coords,
        fill_color=fill_color,
        outline_color=outline_color,
        simplify=simplify,
    )


def create_point(coord: List[float]) -> CircleMarker:
    color = "#fcd34d"
    return CircleMarker(coord=coord, color=color, width=4)


def create_line(coords: List[List[float]]) -> Line:
    color = "#fcd34d"
    simplify = False
    return Line(coords=coords, color=color, width=2, simplify=simplify)


def standardize_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Converts all geometries in a GeoDataFrame to their Multi- counterparts.

    Args:
      gdf (gpd.GeoDataFrame): GeoDataFrame with any geometry types.

    Returns:
      gpd.GeoDataFrame: GeoDataFrame with all geometries as MultiPoint,
      MultiLineString, or MultiPolygon.
    """
    gdf.geometry = gpd.GeoSeries(
        [
            (
                MultiPoint([geom])
                if geom.geom_type == "Point"
                else (
                    MultiLineString([geom])
                    if geom.geom_type == "LineString"
                    else MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom
                )
            )
            for geom in gdf.geometry
        ]
    )
    return gdf


def simplify_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Converts Multi geometries in a GeoDataFrame to their single-part counterparts. If
    Multi geometry, line with longest length returned or polygon with largest area
    returned. First point is returned in event of multipoint.

    Args:
      gdf (gpd.GeoDataFrame): A GeoDataFrame with any geometry types.

    Returns:
      gpd.GeoDataFrame: GeoDataFrame with MultiPoint, MultiLineString, or MultiPolygon
      geometries simplified to Point, LineString, or Polygon where possible.
    """
    gdf.geometry = gpd.GeoSeries(
        [
            (
                geom[0]
                if geom.geom_type == "MultiPoint" and len(geom.geoms) > 0
                else (
                    max(geom.geoms, key=lambda x: x.length)
                    if geom.geom_type == "MultiLineString"
                    else (
                        max(geom.geoms, key=lambda x: x.area)
                        if geom.geom_type == "MultiPolygon"
                        else geom
                    )
                )
            )
            for geom in gdf.geometry
        ]
    )
    return gdf

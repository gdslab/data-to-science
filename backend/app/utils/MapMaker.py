import os

from geojson_pydantic import Feature
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

        # Iterate over each feature and add to map
        for feature in self.features:
            geom_type = feature.geometry.type.lower()
            if geom_type == "point" or geom_type == "multipoint":
                self.map.add_marker(create_point(feature.geometry.coordinates))
            elif geom_type == "linestring" or geom_type == "multilinestring":
                if (
                    len(feature.geometry.coordinates) == 1
                    and len(feature.geometry.coordinates[0]) > 1
                ):
                    self.map.add_line(create_line(feature.geometry.coordinates[0]))
                else:
                    self.map.add_line(create_line(feature.geometry.coordinates))
            elif geom_type == "polygon" or geom_type == "multipolygon":
                if (
                    len(feature.geometry.coordinates) == 1
                    and len(feature.geometry.coordinates[0]) == 1
                ):
                    self.map.add_polygon(
                        create_polygon(feature.geometry.coordinates[0][0])
                    )
                elif (
                    len(feature.geometry.coordinates) >= 1
                    and len(feature.geometry.coordinates[0]) > 1
                ):
                    self.map.add_polygon(
                        create_polygon(feature.geometry.coordinates[0])
                    )
                else:
                    self.map.add_polygon(create_polygon(feature.geometry.coordinates))
            else:
                raise ValueError(f"Unknown geometry type: {geom_type}")

    def save(self, outname: str = "preview_map.png") -> None:
        zoom_level = 16

        image = self.map.render(zoom_level)
        image.save(os.path.join(self.outpath, outname))
        self.preview_img = os.path.join(self.outpath, outname)


def create_polygon(coords: list[list[float, float]]) -> Polygon:
    fill_color = "#fcd34d66"  # 40% opacity
    outline_color = "#fcd34d"
    simplify = False
    return Polygon(
        coords=coords,
        fill_color=fill_color,
        outline_color=outline_color,
        simplify=simplify,
    )


def create_point(coord: list[float, float]) -> CircleMarker:
    color = "#fcd34d"
    return CircleMarker(coord=coord, color=color, width=4)


def create_line(coords: list[list[float, float]]) -> Line:
    color = "#fcd34d"
    simplify = False
    return Line(coords=coords, color=color, width=2, simplify=simplify)

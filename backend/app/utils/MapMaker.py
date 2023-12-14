import os

from staticmap import Polygon, StaticMap


class MapMaker:
    """Used to create static map previews for display on frontend application."""

    def __init__(self, coordinates, outpath):
        self.coordinates = coordinates
        self.outpath = outpath

        size = (128, 128)
        padding = (16, 16)
        basemap = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"

        self.map = StaticMap(size[0], size[1], padding[0], padding[1], basemap)
        self.map.add_polygon(create_polygon(self.coordinates))

    def save(self):
        zoom_level = 14

        image = self.map.render(zoom_level)
        image.save(os.path.join(self.outpath, "preview_map.png"))


def create_polygon(coordinates):
    fill_color = "#fcd34d66"  # 40% opacity
    outline_color = "#fcd34d"
    simplify = False
    return Polygon(coordinates, fill_color, outline_color, simplify)

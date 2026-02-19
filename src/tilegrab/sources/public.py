from .base import TileSource
import logging

logger = logging.getLogger(__name__)


class OSM(TileSource):
    name = "OSM"
    description = "OpenStreetMap imageries"
    output_dir = "osm"
    url_template = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


class ESRIWorldImagery(TileSource):
    name = "ESRIWorldImagery"
    description = "ESRI satellite imageries"
    output_dir = "esri_world"
    url_template = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )
    message = "Warning: Requires a valid ESRI token for production use"

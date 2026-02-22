# sources/restricted.py
from .base import TileSource
import logging

logger = logging.getLogger(__name__)

class GoogleSat(TileSource):
    name = "GoogleSat"
    description = "Google satellite imageries"
    output_dir = "ggl_sat"
    url_template = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    message = (
        "Warning: This tile source violates Google Maps TOS "
        "Section 3.2.4a"
    )
    uid = "gsat"

class Nearmap(TileSource):
    name = "NearmapSat"
    description = "Nearmap satellite imageries"
    url_template = (
        "https://api.nearmap.com/tiles/v3/Vert/{z}/{x}/{y}.png?apikey={token}"
    )
    uid = "nmsat"

    def get_url(self, z: int, x: int, y: int) -> str:
        if not self.api_key:
            logger.error("Nearmap API key missing")
            raise ValueError("API key required for Nearmap")
        return self.url_template.format(
            x=x, y=y, z=z, token=self.api_key
        )

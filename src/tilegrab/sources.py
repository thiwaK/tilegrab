import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TileSource:
    URL_TEMPLATE = ""
    name = None

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        self._headers = headers
        self.api_key = api_key
        logger.debug(f"Initializing TileSource: {self.name}, has_api_key={api_key is not None}")

    def get_url(self, z: int, x: int, y: int) -> str:
        url = self.URL_TEMPLATE.format(x=x, y=y, z=z)
        logger.debug(f"Generated URL for {self.name}: z={z}, x={x}, y={y}")
        return url

    def headers(self) -> Dict[str, str]:
        return self._headers or {
            "referer": "",
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 QGIS/34202/Windows 11 Version 2009",
            "connection": "Keep-Alive ",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,*",
        }


class GoogleSat(TileSource):
    name = "GoogleSat"
    description = "Google satellite imageries"
    URL_TEMPLATE = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    

class OSM(TileSource):
    name = "OSM"
    description = "OpenStreetMap imageries"
    URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

class ESRIWorldImagery(TileSource):
    name = "ESRIWorldImagery"
    description = "ESRI satellite imageries"
    URL_TEMPLATE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

class Nearmap(TileSource):
    name = "NearmapSat"
    description = "Nearmap satellite imageries"
    URL_TEMPLATE = "https://api.nearmap.com/tiles/v3/Vert/{z}/{x}/{y}.png?apikey={token}"

    def get_url(self, z: int, x: int, y: int) -> str:
        if not self.api_key:
            logger.error("Nearmap API key is required but not provided")
            raise AssertionError("API key required for Nearmap")
        url = self.URL_TEMPLATE.format(x=x, y=y, z=z, token=self.api_key)
        logger.debug(f"Generated Nearmap URL: z={z}, x={x}, y={y}")
        return url

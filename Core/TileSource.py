from typing import Dict, Optional


class TileSource:
    URL_TEMPLATE = ""

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        headers: Optional[Dict[str, str]]  = None
    ) -> None:
        self._headers = headers
        self.api_key = api_key

    def get_url(self, z: int, x: int, y: int) -> str:
        return self.URL_TEMPLATE.format(x=x, y=y, z=z)

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
    NAME = "GoogleSat"
    URL_TEMPLATE = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

class OSM(TileSource):
    NAME = "OSM"
    URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

class ESRIWorldImagery(TileSource):
    NAME = "ESRIWorldImagery"
    URL_TEMPLATE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

class Nearmap(TileSource):
    NAME = "NearmapSat"
    URL_TEMPLATE = "https://api.nearmap.com/tiles/v3/Vert/{z}/{x}/{y}.png?apikey={token}"

    def get_url(self, z: int, x: int, y: int) -> str:
        assert self.api_key
        return self.URL_TEMPLATE.format(x=x, y=y, z=z, token=self.api_key)

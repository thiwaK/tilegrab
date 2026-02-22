import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)

class TileSource:
    url_template = ""
    name = None
    api_key = None
    uid = ""

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        headers: Optional[Dict[str, str]] = None) -> None:
        
        self._headers = headers
        self.api_key = api_key
        logger.debug(f"Initializing TileSource: {self.name}, has_api_key={api_key is not None}")

    def get_url(self, z: int, x: int, y: int) -> str:
        url = self.url_template.format(x=x, y=y, z=z)
        logger.debug(f"Generated URL for {self.name}: z={z}, x={x}, y={y}")
        return url

    @property
    def id(self) -> str:
        assert self.uid != "", "invalid source UID"
        return self.uid

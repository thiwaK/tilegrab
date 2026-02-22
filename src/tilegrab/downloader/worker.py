from dataclasses import dataclass
from enum import Enum
import logging
from typing import Union
import requests

from tilegrab.tiles import Tile
from tilegrab.images import TileImage

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    SUCCESS = 200
    SKIP = 100
    UNDEFINED = 900
    EMPTY = 400

@dataclass(frozen=True, slots=True)
class DownloadResult:
    tile:Tile
    status:DownloadStatus
    result:Union[TileImage, None]
    url:str

def download_tile(
    tile: Tile,
    session: requests.Session,
    timeout: float,
) -> DownloadResult:
    x, y, z = tile.index.x, tile.index.y, tile.index.z
    url = tile.url
    
    if not tile.need_download:
        logger.debug(f"Skipping tile: x={x}, y={y}, z={z}")
        return DownloadResult(tile=tile, status=DownloadStatus.SKIP, result=None, url=url)
    
    logger.debug(f"Downloading tile: x={x}, y={y}, z={z}")
    
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image"):
            raise ValueError(f"Unexpected content type: {content_type}")

        if not resp.content:
            return DownloadResult(tile=tile, status=DownloadStatus.EMPTY, result=None, url=url)

        return DownloadResult(
            tile=tile, 
            status=DownloadStatus.SUCCESS, 
            result=TileImage(tile=tile, image=resp.content), 
            url=url)

    except requests.Timeout:
        logger.warning("Timeout fetching tile %s/%s/%s", z, x, y)
    except requests.RequestException as e:
        logger.warning("Request failed %s/%s/%s: %s", z, x, y, e)
    except Exception:
        logger.exception("Unexpected error %s/%s/%s", z, x, y)

    return DownloadResult(tile=tile, status=DownloadStatus.UNDEFINED, result=None, url=url)
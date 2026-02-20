import logging
import requests

from tilegrab.tiles import Tile
from tilegrab.images import TileImage

logger = logging.getLogger(__name__)


def download_tile(
    tile: Tile,
    session: requests.Session,
    timeout: float,
) -> TileImage | None:
    x, y, z = tile.index.x, tile.index.y, tile.index.z
    url = tile.url

    logger.debug(f"Downloading tile: x={x}, y={y}, z={z}")

    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image"):
            raise ValueError(f"Unexpected content type: {content_type}")

        if not resp.content:
            return None

        return TileImage(tile=tile, image=resp.content)

    except requests.Timeout:
        logger.warning("Timeout fetching tile %s/%s/%s", z, x, y)
    except requests.RequestException as e:
        logger.warning("Request failed %s/%s/%s: %s", z, x, y, e)
    except Exception:
        logger.exception("Unexpected error %s/%s/%s", z, x, y)

    return None
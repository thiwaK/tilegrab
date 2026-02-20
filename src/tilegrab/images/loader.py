import re
import logging
from pathlib import Path
from tilegrab.images.image import TileImage
from tilegrab.tiles import TileCollection

logger = logging.getLogger(__name__)


_TILE_RE = re.compile(r"^(\d+)_(\d+)_(\d+)\.\w+$")


def load_images(
    path: Path,
    tiles: TileCollection,
) -> list[TileImage]:
    images: list[TileImage] = []
    files = [p for p in path.glob("*") if p.is_file()]

    for tile in tiles:
        for f in files:
            m = _TILE_RE.match(f.name)
            if not m:
                continue

            z, x, y = map(int, m.groups())
            if (x, y, z) == (tile.index.x, tile.index.y, tile.index.z):
                with open(f, "rb") as fp:
                    img = TileImage(tile, fp.read())
                    img.path = f
                    images.append(img)
                break

    logger.info("Loaded %d images", len(images))
    return images
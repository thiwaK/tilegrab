import logging
from PIL import Image
from tilegrab.images import TileImageCollection

logger = logging.getLogger(__name__)

def mosaic(images: TileImageCollection) -> Image.Image:
    if not images:
        raise ValueError("No images to mosaic")

    xs = [i.index.x for i in images]
    ys = [i.index.y for i in images]

    minx, miny = min(xs), min(ys)
    tile_w, tile_h = images[0].width, images[0].height

    width = (max(xs) - minx + 1) * tile_w
    height = (max(ys) - miny + 1) * tile_h

    out = Image.new("RGB", (width, height))

    for img in images:
        px = (img.index.x - minx) * tile_w
        py = (img.index.y - miny) * tile_h
        out.paste(img.image, (px, py))

    return out
import logging
from typing import Iterator
import numpy as np
from PIL import Image as PILImage
from numpy.lib.stride_tricks import sliding_window_view

logger = logging.getLogger(__name__)

def group_image(
    image: PILImage.Image,
    tile_w: int,
    tile_h: int,
    group_w: int,
    group_h: int,
) -> Iterator:
    arr = np.asarray(image)
    kh, kw = tile_h * group_h, tile_w * group_w

    view = sliding_window_view(arr, (kh, kw, arr.shape[2]))
    view = view[..., 0, :, :, :]
    OH, OW = view.shape[:2]

    for i in range(0, OH, group_h*tile_h):
        for j in range(0, OW, group_w*tile_w):
            patch = view[i, j]
            if not (patch == 0).all():
                yield PILImage.fromarray(patch)
            else:
                logger.debug(f"Skip no-data group {i}{j}")

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union
from tilegrab.images.image import TileImage
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class ImageCollectionBounds:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

WEB_MERCATOR_EXTENT = 20037508.342789244
EPSG = 3857

class TileImageCollection:
    
    def __init__(self, path: Union[Path, str], images: list[TileImage] | None = None):
        self.path = Path(path)
        self.images: list[TileImage] = images or []
        self.width = 0
        self.height = 0
        self.minx, self.maxx = 0, 0
        self.miny, self.maxy = 0, 0

        self.update_collection_dim()

    def __len__(self):
        return len(self.images)

    def __iter__(self):
        return iter(self.images)

    def __getitem__(self, index):
        return self.images[index]

    def append(self, image: TileImage):
        self.images.append(image)

    @property
    def zoom(self) -> int:
        if not self.images:
            raise ValueError("Empty collection")
        return self.images[0].tile.index.z

    @classmethod
    def from_images(
        cls,
        images: list[TileImage],
        path: Union[Path, str],
        save: bool = True,
    ):
        col = cls(path=path, images=list(images))

        if save:
            for img in col.images:
                img.path = col.path / img.name
                img.save()

        return col

    def update_collection_dim(self):
        
        if not self.images:
            logger.warning("Attempting to update collection dimensions with no images")
            return

        x = [img.index.x for img in self.images]
        y = [img.index.y for img in self.images]
        minx, maxx = min(x), max(x)
        miny, maxy = min(y), max(y)
        self.minx, self.maxx = minx, maxx
        self.miny, self.maxy = miny, maxy
        logger.debug(f"Tile range x=({self.minx}, {self.maxx}); y=({self.miny}, {self.maxy})")

        self.width = int((maxx - minx + 1) * self.images[0].width)
        self.height = int((maxy - miny + 1) * self.images[0].height)
       
        
        logger.info(f"Collection dimensions calculated: {self.width}x{self.height}")

    @property
    def bounds(self) -> ImageCollectionBounds:
        n = 2**self.zoom
        tile_size_m = 2 * WEB_MERCATOR_EXTENT / n

        xmin = (WEB_MERCATOR_EXTENT * -1) + self.minx * tile_size_m
        xmax = (WEB_MERCATOR_EXTENT * -1) + (self.maxx + 1) * tile_size_m

        ymax = WEB_MERCATOR_EXTENT - self.miny * tile_size_m
        ymin = WEB_MERCATOR_EXTENT - (self.maxy + 1) * tile_size_m

        return ImageCollectionBounds(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)


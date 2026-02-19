import logging
from typing import List

from tilegrab.tiles import Tile
from tilegrab.tiles.collection import TileCollection


logger = logging.getLogger(__name__)

class TilesByBBox(TileCollection):

    def build_tile_cache(self) -> List[Tile]:
        logger.info(f"Building tiles by bounding box at zoom level {self.zoom}")
        bbox = self.geo_dataset.bbox
        logger.debug(
            f"BBox coordinates: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}"
        )

        self._cache = list(self.tiles_in_bound(clip_to_shape=False))
        logger.debug(f"Generated {len(self)} tiles from bounding box")
        return self._cache

class TilesByShape(TileCollection):

    def build_tile_cache(self) -> List[Tile]:

        logger.info(f"Building tiles by shape intersection at zoom level {self.zoom}")
        
        bbox = self.geo_dataset.bbox
        logger.debug(
            f"Checking tiles within bbox: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}"
        )

        self._cache = list(self.tiles_in_bound(clip_to_shape=True))
        logger.info(f"Generated {len(self)} tiles from shape intersection")
        return self._cache

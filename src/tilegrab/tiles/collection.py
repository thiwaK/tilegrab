import logging
import math
from typing import Iterator, List
from abc import ABC, abstractmethod

from tilegrab.dataset import GeoDataset
from tilegrab.sources.base import TileSource
from tilegrab.tiles import Tile
from box import Box

logger = logging.getLogger(__name__)

EPSILON = 1e-14
LL_EPSILON = 1e-11


class TileCollection(ABC):

    MIN_X: float = 0
    MAX_X: float = 0
    MIN_Y: float = 0
    MAX_Y: float = 0
    _cache: List[Tile]
    _tile_count: int = 0


    def __len__(self):
        return self._tile_count

    def __iter__(self):
        for t in self._cache:
            yield t.index.z, t.index.x, t.index.y
    
    def __repr__(self) -> str:
        return f"TileCollection; len={len(self)}; x-extent=({self.geo_dataset.bbox.minx:.3f}-{self.geo_dataset.bbox.maxx:.3f}); y-extent=({self.geo_dataset.bbox.miny:.3f}-{self.geo_dataset.bbox.maxy:.3f})"

    def __init__(
            self, geo_dataset: GeoDataset, tile_source:TileSource , zoom: int, safe_limit: int = 250):
        
        self.zoom = zoom
        self.safe_limit = safe_limit
        self.geo_dataset = geo_dataset
        self.tile_source = tile_source

        logger.info(
            f"Initializing TileCollection: zoom={zoom}, safe_limit={safe_limit}"
        )

        # assert feature.bbox.minx < feature.bbox.maxx
        # assert feature.bbox.miny < feature.bbox.maxy

        self.build_tile_cache()

        if len(self) > safe_limit:
            logger.error(f"Tile count exceeds safe limit: {len(self)} > {safe_limit}")
            raise ValueError(
                f"Your query excedes the hard limit {len(self)} > {safe_limit}"
            )

        logger.info(f"TileCollection initialized with {len(self)} tiles")

    @property
    def to_list(self) -> List[Tile]:
        cache = list(self._cache)
        if cache is None or len(cache) < 1:
            logger.debug("Building tile cache from to_list property")
            self.build_tile_cache()
            if len(self) > self.safe_limit:
                logger.error(
                    f"Tile count exceeds safe limit in to_list: {len(self)} > {self.safe_limit}"
                )
                raise ValueError("Too many tiles")
        assert self._cache
        return list(self._cache)
    
    @abstractmethod
    def build_tile_cache(self) -> List[Tile]:
        raise NotImplementedError

    def tiles_in_bound(self, clip_to_shape=False) -> Iterator[Tile]:
        
        bbox = self.geo_dataset.bbox

        def tile(lng, lat, zoom):
            logger.debug(f"Creating new Tile; lat={lat}; lng={lng}")

            x = lng / 360.0 + 0.5
            sinlat = math.sin(math.radians(lat))

            try:
                y = 0.5 - 0.25 * math.log((1.0 + sinlat) / (1.0 - sinlat)) / math.pi
            except:
                raise

            Z2 = math.pow(2, zoom)

            if x <= 0:
                xtile = 0
            elif x >= 1:
                xtile = int(Z2 - 1)
            else:
                # To address loss of precision in round-tripping between tile
                # and lng/lat, points within EPSILON of the right side of a tile
                # are counted in the next tile over.
                xtile = int(math.floor((x + EPSILON) * Z2))

            if y <= 0:
                ytile = 0
            elif y >= 1:
                ytile = int(Z2 - 1)
            else:
                ytile = int(math.floor((y + EPSILON) * Z2))

            
            return Box({"x": xtile, "y": ytile})

        w, s, e, n = bbox.minx, bbox.miny, bbox.maxx, bbox.maxy
        if s < -85.051129 or n > 85.051129:
            logger.warning("Your geometry bounds exceed the Web Mercator's limits")
            logger.info("Clipping bounds for Web Mercator's limits")

            w = max(-180.0, w)
            s = max(-85.051129, s)
            e = min(180.0, e)
            n = min(85.051129, n)

        ul_tile = tile(w, n, self.zoom)
        lr_tile = tile(e - LL_EPSILON, s + LL_EPSILON, self.zoom)
        logger.debug(f"UpperLeft Tile=({ul_tile}); LowerRight Tile=({lr_tile})")

        self._tile_count = 0
        self.MAX_X, self.MIN_X = lr_tile.x, ul_tile.x
        self.MAX_Y, self.MIN_Y = lr_tile.y, ul_tile.y
        
        logger.info(
            f"TileCollection bounds: x=({self.MIN_X}, {self.MAX_X}) y=({self.MIN_Y}, {self.MAX_Y})"
        )

        for i in range(ul_tile.x, lr_tile.x + 1):
            for j in range(ul_tile.y, lr_tile.y + 1):
                t = Tile(i, j, self.zoom, self.tile_source)
                if clip_to_shape:
                    condition = t.polygon_bounds.intersects(self.geo_dataset.geometry.geometry).any()
                    if not condition:
                        logger.debug(
                            f"Tile excluded: z={self.zoom}, x={i}, y={j}"
                            )
                        continue
                self._tile_count += 1
                yield t


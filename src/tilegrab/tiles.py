import logging
import math
from typing import Any, List, Tuple
import mercantile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
from .dataset import GeoDataset
from box import Box

logger = logging.getLogger(__name__)

@dataclass
class Tile:
    x: int = 0
    y: int = 0
    z: int = 0

    def __post_init__(self):
        self._position = None
        logger.debug(f"Tile created: z={self.z}, x={self.x}, y={self.y}")

    # @classmethod
    # def from_tuple(cls, t: tuple[int, int, int]) -> "Tile":
    #     logger.debug(f"Creating Tile from tuple: {t}")
    #     return cls(*t)
    
    @property
    def url(self) -> Union[str, None]:
        return self._url

    @url.setter
    def url(self, value: str):
        logger.debug(f"Tile URL set for z={self.z},x={self.x},y={self.y}")
        self._url = value

    @property
    def position(self) -> Box:
        if self._position is None:
            logger.error(f"Tile position not set: z={self.z}, x={self.x}, y={self.y}")
            raise RuntimeError("Image does not have an position")
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float]):
        x, y = self.x - value[0], self.y - value[1]
        self._position = Box({'x': x, 'y': y})
        logger.debug(f"Tile position calculated: x={x}, y={y}")

class TileCollection(ABC):
    
    MIN_X: float = 0
    MAX_X: float = 0
    MIN_Y: float = 0
    MAX_Y: float = 0
    _cache: Union[List[Tile], None] = None

    @abstractmethod
    def _build_tile_cache(self) -> list[Tile]:
        raise NotImplementedError

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for t in self._cache:  # type: ignore
            yield t.z, t.x, t.y

    def __init__(self, feature: GeoDataset, zoom: int, SAFE_LIMIT: int = 250):
        self.zoom = zoom
        self.SAFE_LIMIT = SAFE_LIMIT
        self.feature = feature

        logger.info(f"Initializing TileCollection: zoom={zoom}, safe_limit={SAFE_LIMIT}")

        assert feature.bbox.minx < feature.bbox.maxx
        assert feature.bbox.miny < feature.bbox.maxy

        self._build_tile_cache()
        self._update_min_max()
        
        if len(self) > SAFE_LIMIT:
            logger.error(f"Tile count exceeds safe limit: {len(self)} > {SAFE_LIMIT}")
            raise ValueError(
                f"Your query excedes the hard limit {len(self)} > {SAFE_LIMIT}"
            )
        
        logger.info(f"TileCollection initialized with {len(self)} tiles")

    def __repr__(self) -> str:
        return f"TileCollection; len={len(self)}; x-extent=({self.feature.bbox.minx}-{self.feature.bbox.maxx}); y-extent=({self.feature.bbox.miny}-{self.feature.bbox.maxy})"

    def tile_bounds(self, x, y, z) -> Tuple[float, float, float, float]:
        n = 2**z

        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0

        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

        logger.debug(f"Tile bounds calculated for z={z},x={x},y={y}: ({lon_min},{lat_min},{lon_max},{lat_max})")
        return lon_min, lat_min, lon_max, lat_max

    @property
    def to_list(self) -> list[Tile]:
        if self._cache is None:
            logger.debug("Building tile cache from to_list property")
            self._build_tile_cache()
            self._update_min_max()
            if len(self) > self.SAFE_LIMIT:
                logger.error(f"Tile count exceeds safe limit in to_list: {len(self)} > {self.SAFE_LIMIT}")
                raise ValueError("Too many tiles")
        
        assert self._cache
        return self._cache

    def _update_min_max(self):
        assert self._cache
        x = [t.x for t in self._cache]
        y = [t.y for t in self._cache]
        self.MAX_X, self.MIN_X = max(x), min(x)
        self.MAX_Y, self.MIN_Y = max(y), min(y)

        logger.info(f"TileCollection bounds: x=({self.MIN_X}, {self.MAX_X}) y=({self.MIN_Y}, {self.MAX_Y})")

        for i in range(len(self._cache)):
            self._cache[i].position = self.MIN_X, self.MIN_Y

class TilesByBBox(TileCollection):
    
    def _build_tile_cache(self) -> list[Tile]:
        logger.info(f"Building tiles by bounding box at zoom level {self.zoom}")
        bbox = self.feature.bbox
        logger.debug(f"BBox coordinates: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}")
        
        self._cache = [
            Tile(t.x, t.y, t.z)
            for t in mercantile.tiles(
                bbox.minx,
                bbox.miny,
                bbox.maxx,
                bbox.maxy,
                self.zoom,
            )
        ]
        
        logger.debug(f"Generated {len(self._cache)} tiles from bounding box")
        return self._cache

class TilesByShape(TileCollection):

    def _build_tile_cache(self) -> list[Tile]:
        from shapely.geometry import box

        logger.info(f"Building tiles by shape intersection at zoom level {self.zoom}")
        geometry = self.feature.shape
        if hasattr(geometry, "geometry"):
            geometry = geometry.geometry.unary_union
            logger.debug("Converted GeoDataFrame geometry to unary_union")

        tiles = []
        bbox = self.feature.bbox
        logger.debug(f"Checking tiles within bbox: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}")
        
        for t in mercantile.tiles(
            bbox.minx,
            bbox.miny,
            bbox.maxx,
            bbox.maxy,
            self.zoom,
        ):
            tb = box(*self.tile_bounds(t.x, t.y, t.z))
            if tb.intersects(geometry):
                tiles.append(Tile(t.x, t.y, t.z))
        
        self._cache = tiles
        logger.info(f"Generated {len(tiles)} tiles from shape intersection")
        return tiles
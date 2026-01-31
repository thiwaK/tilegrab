from box import Box
import math
from typing import List, Optional, Tuple
import mercantile
from abc import ABC, abstractmethod
from typing import Union
from .dataset import GeoDataset


class Tiles(ABC):
    
    MIN_X: int = 0
    MAX_X: int = 0
    MIN_Y: int = 0
    MAX_Y: int = 0
    _cache: Union[List[Box], None] = None

    @abstractmethod
    def _build_tile_cache(self) -> list[Box]:
        raise NotImplementedError

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        assert self._cache
        for t in self._cache:
            yield t.z, t.x, t.y

    def __init__(self, feature: GeoDataset, zoom: int, SAFE_LIMIT: int = 250):
        self.zoom = zoom
        self.SAFE_LIMIT = SAFE_LIMIT
        self.feature = feature

        assert feature.bbox.minx < feature.bbox.maxx
        assert feature.bbox.miny < feature.bbox.maxy

        self._build_tile_cache()
        self._update_min_max()
        
        if len(self) > SAFE_LIMIT:
            raise ValueError(
                f"Your query excedes the hard limit {len(self)} > {SAFE_LIMIT}"
            )

    def __repr__(self) -> str:
        return f"TileCollection; len={len(self)}; x-extent=({self.feature.bbox.minx}-{self.feature.bbox.maxx}); y-extent=({self.feature.bbox.miny}-{self.feature.bbox.maxy})"

    def tile_bounds(self, x, y, z) -> Tuple[float, float, float, float]:
        n = 2**z

        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0

        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

        return lon_min, lat_min, lon_max, lat_max


    @property
    def to_list(self) -> list[Box]:
        if self._cache is None:
            self._build_tile_cache()
            self._update_min_max()
            if len(self) > self.SAFE_LIMIT:
                raise ValueError("Too many tiles")
        
        assert self._cache
        return self._cache

    @property
    def x_extent(self):
        return (self.feature.bbox.maxx - self.feature.bbox.minx) + 1

    @property
    def y_extent(self):
        return (self.feature.bbox.maxy - self.feature.bbox.miny) + 1

    def _update_min_max(self):
        assert self._cache
        x = [t.x  for t in self._cache]
        y = [t.y  for t in self._cache]
        self.MAX_X, self.MIN_X = max(x), min(x)
        self.MAX_Y, self.MIN_Y = max(y), min(y)

class TilesByBBox(Tiles):
    
    def _build_tile_cache(self) -> list[Box]:
        self._cache =  [
            Box({"z": t.z, "x": t.x, "y": t.y})
            for t in mercantile.tiles(
                self.feature.bbox.minx,
                self.feature.bbox.miny,
                self.feature.bbox.maxx,
                self.feature.bbox.maxy,
                self.zoom,
            )
        ]

        return self._cache

class TilesByShape(Tiles):

    def _build_tile_cache(self) -> list[Box]:
        from shapely.geometry import box

        geometry = self.feature.shape
        if hasattr(geometry, "geometry"):
            geometry = geometry.geometry.unary_union

        tiles = []
        for t in mercantile.tiles(
            self.feature.bbox.minx,
            self.feature.bbox.miny,
            self.feature.bbox.maxx,
            self.feature.bbox.maxy,
            self.zoom,
        ):
            tb = box(*self.tile_bounds(t.x, t.y, t.z))
            if tb.intersects(geometry):
                tiles.append(Box({"z": t.z, "x": t.x, "y": t.y}))
        
        self._cache = tiles
        return tiles
    

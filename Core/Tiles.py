from box import Box
import math
from typing import List, Tuple
import mercantile

from Core import GeoDataset


class Tiles:
    
    MIN_X: int = 0
    MAX_X: int = 0
    MIN_Y: int = 0
    MAX_Y: int = 0

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for t in self.to_list:
            yield t.z, t.x, t.y

    def __init__(self, feature: GeoDataset, zoom: int, SAFE_LIMIT: int = 250):
        self._cache = None

        assert feature.bbox.minx < feature.bbox.maxx
        assert feature.bbox.miny < feature.bbox.maxy

        if len(self) > SAFE_LIMIT:
            raise ValueError(
                f"Your query excedes the hard limit {len(self)} > {SAFE_LIMIT}"
            )

        self.zoom = zoom
        self.SAFE_LIMIT = SAFE_LIMIT
        self.feature = feature

    def tile_bounds(self, x, y, z) -> Tuple[float, float, float, float]:
        n = 2**z

        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0

        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

        return lon_min, lat_min, lon_max, lat_max

    @property
    def to_list(self) -> list[Box]:
        if self._cache:
            return self._cache
        else:
            return []

    # @property
    # def tiles_w(self):
    #     return (self.bbox.maxx - self.bbox.minx) + 1

    # @property
    # def tiles_h(self):
    #     return (self.bbox.maxy - self.bbox.miny) + 1

    def _update_min_max(self, tile_list):
        x = [t.x  for t in tile_list]
        y = [t.y  for t in tile_list]
        self.MAX_X, self.MIN_X = max(x), min(x)
        self.MAX_Y, self.MIN_Y = max(y), min(y)

class TilesByBBox(Tiles):
    
    def __new__(cls):
        pass

    @property
    def from_bbox(self) -> List[Box]:
        
        if self._cache is not None:
            return self._cache

        tiles = [
            Box({"z": t.z, "x": t.x, "y": t.y})
            for t in mercantile.tiles(
                self.feature.bbox.minx,
                self.feature.bbox.miny,
                self.feature.bbox.maxx,
                self.feature.bbox.maxy,
                self.zoom,
            )
        ]

        self._cache = tiles
        self._update_min_max(tiles)
        return tiles

class TilesByShape(Tiles):
    
    @property
    def from_shape(self) -> List[Box]:

        from shapely.geometry import box

        if self._cache is not None:
            return self._cache

        geometry = self.feature.shape
        if hasattr(geometry, "geometry"):
            geometry = geometry.geometry.unary_union

        tiles_bbox = [
            Box({"z": t.z, "x": t.x, "y": t.y})
            for t in mercantile.tiles(
                self.feature.bbox.minx,
                self.feature.bbox.miny,
                self.feature.bbox.maxx,
                self.feature.bbox.maxy,
                self.zoom,
            )
        ]

        if not tiles_bbox:
            return []

        # tiles_intersects = [
        #     Box({"z": tt[3], "x": tt[1], "y": tt[2]})
        #     for tt in [
        #         (box(*self.tile_bounds(t.x, t.y, t.z)), t.x, t.y, t.z)
        #         for t in tiles_bbox
        #     ]
        #     if tt[0].intersects(geometry)
        # ]

        tiles_intersects = []
        for t in tiles_bbox:
            tb = box(*self.tile_bounds(t.x, t.y, t.z))   # tb is a shapely Polygon
            if tb.intersects(geometry):                   # geometry must be a shapely geometry too
                tiles_intersects.append(Box({"z": t.z, "x": t.x, "y": t.y}))

        self._cache = tiles_intersects
        self._update_min_max(tiles_intersects)
        return tiles_intersects

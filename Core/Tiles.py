from box import Box
from dataclasses import dataclass
import math
from shapely.geometry import box
from typing import List, Tuple

from Core import GeoDataset


@dataclass
class Tiles:
    feature: GeoDataset
    zoom: int
    SAFE_LIMIT: int = 250

    def __len__(self):
        return sum(1 for _ in self)
    
    def __iter__(self):
        for t in self.to_list:
            yield t.z, t.x, t.y

    def __post_init__(self):
        self._cache_box = None
        self._cache = None

        assert self.feature.bbox.minx < self.feature.bbox.maxx
        assert self.feature.bbox.miny < self.feature.bbox.maxy

        if len(self) > self.SAFE_LIMIT:
            raise ValueError(f"Your query excedes the hard limit {len(self)} > {self.SAFE_LIMIT}")

    def _lon_to_x(self, lon, zoom):
        n = 2**zoom
        return int((lon + 180.0) / 360.0 * n)

    def _lat_to_y(self, lat, zoom):
        lat_rad = math.radians(lat)
        n = 2**zoom
        return int(
            (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
            / 2.0
            * n
        )

    def _tiles_in_bbox(self) -> List[Box]:

        if self._cache is not None:
            return self._cache

        x_min = self._lon_to_x(self.feature.bbox.minx, self.zoom)
        x_max = self._lon_to_x(self.feature.bbox.maxx, self.zoom)
        y_min = self._lat_to_y(self.feature.bbox.maxy, self.zoom)
        y_max = self._lat_to_y(self.feature.bbox.miny, self.zoom)

        tiles = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                tiles.append(Box({"z": self.zoom, "x": x, "y": y}))

        self._cache = tiles
        return tiles

    @property
    def from_bbox(self):
        import mercantile

        if self._cache_box is not None:
            return self._cache_box

        tiles = [
            Box({"z": t.z, "x": t.x, "y": t.y})
            for t in mercantile.tiles(self.feature.bbox.minx, self.feature.bbox.miny, self.feature.bbox.maxx, self.feature.bbox.maxy, self.zoom)
        ]

        self._cache_box = tiles
        self._cache = None
        return tiles

    @property
    def from_shape(self):

        if self._cache is not None:
            return self._cache
        
        geometry = self.feature.shape
        tiles_bbox = self.from_bbox
        tiles = [tt for tt in [box(*self.tile_bounds(t.x, t.y, t.z)) for t in tiles_bbox] if tt.intersects(geometry)]

        self._cache = tiles
        self._cache_box = None
        return tiles

    def tile_bounds(self, x, y, z) -> Tuple[float, float, float, float]:
        n = 2 ** z

        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0

        lat_min = math.degrees(
            math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
        )
        lat_max = math.degrees(
            math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        )

        return lon_min, lat_min, lon_max, lat_max

    # @property
    # def to_list(self) -> list[Box]:
    #     return self._tiles_in_bbox()

    # @property
    # def tiles_w(self):
    #     return (self.bbox.maxx - self.bbox.minx) + 1
    
    # @property
    # def tiles_h(self):
    #     return (self.bbox.maxy - self.bbox.miny) + 1



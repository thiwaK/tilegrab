import logging
import math
from typing import Iterator, List, Tuple, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .dataset import GeoDataset
from box import Box
from functools import cache

logger = logging.getLogger(__name__)

EPSILON = 1e-14
LL_EPSILON = 1e-11


@dataclass
class Tile:
    x: int = 0
    y: int = 0
    z: int = 0

    def __post_init__(self):
        self._position = None
        logger.debug(f"Tile created: x={self.x}, y={self.y}, z={self.z}")

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
            raise RuntimeError("Image does not have a position")
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float]):
        x, y = self.x - value[0], self.y - value[1]
        self._position = Box({"x": x, "y": y})
        logger.debug(f"Tile position calculated: x={x}, y={y}")


class TileCollection(ABC):

    MIN_X: float = 0
    MAX_X: float = 0
    MIN_Y: float = 0
    MAX_Y: float = 0
    _cache: List[Tile]
    _tile_count: int = 0

    @abstractmethod
    def _build_tile_cache(self) -> List[Tile]:
        raise NotImplementedError

    def __len__(self):
        return self._tile_count

    def __iter__(self):
        for t in self._cache:  # type: ignore
            yield t.z, t.x, t.y
    
    def __repr__(self) -> str:
        return f"TileCollection; len={len(self)}; x-extent=({self.feature.bbox.minx}-{self.feature.bbox.maxx}); y-extent=({self.feature.bbox.miny}-{self.feature.bbox.maxy})"

    def __init__(self, feature: GeoDataset, zoom: int, SAFE_LIMIT: int = 250):
        self.zoom = zoom
        self.SAFE_LIMIT = SAFE_LIMIT
        self.geo_dataset = geo_dataset

        logger.info(
            f"Initializing TileCollection: zoom={zoom}, safe_limit={SAFE_LIMIT}"
        )

        # assert feature.bbox.minx < feature.bbox.maxx
        # assert feature.bbox.miny < feature.bbox.maxy

        self._build_tile_cache()

        if len(self) > SAFE_LIMIT:
            logger.error(f"Tile count exceeds safe limit: {len(self)} > {SAFE_LIMIT}")
            raise ValueError(
                f"Your query excedes the hard limit {len(self)} > {SAFE_LIMIT}"
            )

        logger.info(f"TileCollection initialized with {len(self)} tiles")

    def tile_bounds(self, x, y, z) -> Tuple[float, float, float, float]:
        n = 2**z

        lon_min = x / n * 360.0 - 180.0
        lon_max = (x + 1) / n * 360.0 - 180.0

        lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))

        logger.debug(
            f"Tile bounds calculated for z={z},x={x},y={y}: ({lon_min},{lat_min},{lon_max},{lat_max})"
        )
        return lon_min, lat_min, lon_max, lat_max

    @property
    @cache
    def to_list(self) -> List[Tile]:
        cache = list(self._cache)
        if cache is None or len(cache) < 1:
            logger.debug("Building tile cache from to_list property")
            self._build_tile_cache()
            if len(self) > self.SAFE_LIMIT:
                logger.error(
                    f"Tile count exceeds safe limit in to_list: {len(self)} > {self.SAFE_LIMIT}"
                )
                raise ValueError("Too many tiles")
        assert self._cache
        return list(self._cache)

    def tile_bbox_geojson(self, x: int, y: int, z: int) -> dict:
        min_lon, min_lat, max_lon, max_lat = self.tile_bbox(x, y, z)
        return {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [min_lon, max_lat],
                [max_lon, max_lat],
                [max_lon, min_lat],
                [min_lon, min_lat]
            ]]
        }

    def tile_bbox(self, x: int, y: int, z: int) -> Tuple[float, float, float, float]:
        """
        Return bounding box of a Slippy Map tile as (min_lon, min_lat, max_lon, max_lat).
        x, y are tile indices at zoom z.
        """
        n = 2.0 ** z
        min_lon = x / n * 360.0 - 180.0
        max_lon = (x + 1) / n * 360.0 - 180.0

        def tile_y_to_lat(yt: float) -> float:
            # convert fractional tile y to latitude in degrees
            merc_y = math.pi * (1 - 2 * yt / n)
            lat_rad = math.atan(math.sinh(merc_y))
            return math.degrees(lat_rad)

        max_lat = tile_y_to_lat(y)        # top edge (smaller y => larger lat)
        min_lat = tile_y_to_lat(y + 1)    # bottom edge

        return (min_lon, min_lat, max_lon, max_lat)

    def _tiles_in_bounds(self, clip_to_shape=False) -> Iterator[Tile]:
        
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
                if clip_to_shape:
                    from shapely.geometry import box
                    tb = box(*self.tile_bbox(i,j,self.zoom))
                    if not tb.intersects(self.geo_dataset.geometry.geometry).any():
                        logger.debug(f"Tile excluded: z={self.zoom}, x={i}, y={j}")
                        continue
                self._tile_count += 1
                t = Tile(i, j, self.zoom)
                t.position = self.MIN_X, self.MIN_Y
                yield t


class TilesByBBox(TileCollection):

    def _build_tile_cache(self) -> List[Tile]:
        logger.info(f"Building tiles by bounding box at zoom level {self.zoom}")
        bbox = self.geo_dataset.bbox
        logger.debug(
            f"BBox coordinates: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}"
        )

        self._cache = list(self._tiles_in_bounds(True))
        logger.debug(f"Generated {len(self)} tiles from bounding box")
        return self._cache


class TilesByShape(TileCollection):

    def _build_tile_cache(self) -> List[Tile]:

        logger.info(f"Building tiles by shape intersection at zoom level {self.zoom}")
        
        bbox = self.geo_dataset.bbox
        logger.debug(
            f"Checking tiles within bbox: minx={bbox.minx}, miny={bbox.miny}, maxx={bbox.maxx}, maxy={bbox.maxy}"
        )

        self._cache = list(self._tiles_in_bounds(True))
        logger.info(f"Generated {len(self)} tiles from shape intersection")
        return self._cache

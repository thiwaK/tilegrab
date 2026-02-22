import logging
from dataclasses import dataclass
from tilegrab.sources.base import TileSource
import shapely
import math

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TileIndex:
    x: int
    y: int
    z: int

@dataclass(frozen=True, slots=True)
class GeoBounds:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

class Tile:
    """
    A single tile.
    """

    __slots__ = ("_index", "_bounds", "_url", "_polygon_bounds", "_geojson_bounds", "_download")

    def __init__(self, x: int, y: int, z: int, source: TileSource):
        self._index = TileIndex(x=x, y=y, z=z)
        self._bounds = self.tile_bounds(x=x, y=y, z=z)
        self._url = source.get_url(x=x, y=y, z=z)
        self._polygon_bounds = None
        self._geojson_bounds = None
        self._download: bool = True
        logger.debug("Tile created: index=%s; geobound=%s", self._index, self._bounds)
    
    def __eq__(self, other):
        if not isinstance(other, Tile):
            return NotImplemented
        
        return (
                self.index.x, self.index.y, self.index.z
            ) == (
                other.index.x, other.index.y, other.index.z
            )

    @property
    def index(self) -> TileIndex:
        return self._index

    @property
    def bounds(self) -> GeoBounds:
        return self._bounds

    @property
    def url(self) -> str:
        return self._url
    
    def tile_bounds(self, x: int, y: int, z: int) -> GeoBounds:
        """
        Return GeoBounds of a Slippy Map tile.
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

        
        return GeoBounds(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)

    @property
    def geojson_bounds(self) -> dict:
        if not self._geojson_bounds:
            min_lon, min_lat, max_lon, max_lat = self._bounds.min_lon, self._bounds.min_lat, self._bounds.max_lon, self._bounds.max_lat
            self._geojson_bounds = {
                "type": "Polygon",
                "coordinates": [[
                    [min_lon, min_lat],
                    [min_lon, max_lat],
                    [max_lon, max_lat],
                    [max_lon, min_lat],
                    [min_lon, min_lat]
                ]]
            }
        return self._geojson_bounds

    @property
    def polygon_bounds(self) -> shapely.Polygon:
        if not self._polygon_bounds:
            from shapely.geometry import box
            self._polygon_bounds = box(self._bounds.min_lon, self._bounds.min_lat, self._bounds.max_lon, self._bounds.max_lat)
        return self._polygon_bounds
    
    @property
    def need_download(self) -> bool:
        return self._download
    
    @need_download.setter
    def need_download(self, value:bool):
        self._download = value
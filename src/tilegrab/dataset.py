from dataclasses import dataclass
import logging
from pathlib import Path
from box import Box
from typing import Union
from functools import cache

logger = logging.getLogger(__name__)

TILE_EPSG = 4326 #Web Mercator - 3857 | 4326 - WGS84

class GeoDataset:
    @property
    @cache
    def bbox(self):
        minx, miny, maxx, maxy = self.source.total_bounds
        bbox_dict = Box({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
        logger.debug(f"Bbox calculated: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")
        return bbox_dict
    
    @property
    def shape(self):
        return self.source.geometry
    
    @property
    def x_extent(self):
        minx, _, maxx, _ = self.source.total_bounds
        extent = (maxx - minx) + 1
        logger.debug(f"X extent calculated: {extent}")
        return extent

    @property
    def y_extent(self):
        _, miny, _, maxy = self.source.total_bounds
        extent = (maxy - miny) + 1
        logger.debug(f"Y extent calculated: {extent}")
        return extent

    def buffer(self, distance: int) -> None:
        logger.debug(f"Buffering geometry by {distance} units")
        self.source.geometry.buffer(distance)

    def __init__(self, source_path: Union[Path, str]):
        import geopandas as gpd
        from pyproj import CRS

        source_path = Path(source_path)
        logger.info(f"Loading GeoDataset from: {source_path}")
        
        try:
            gdf = gpd.read_file(source_path)
        except Exception as e:
            logger.error(f"Failed to read geospatial file: {source_path}", exc_info=True)
            raise
        
        epsg = None

        if gdf.crs is not None:
            try:
                epsg = CRS.from_user_input(gdf.crs).to_epsg()
                logger.debug(f"Detected CRS EPSG code: {epsg}")
            except Exception as e:
                logger.critical(f"Unable to parse CRS from dataset: {gdf.crs}", exc_info=True)
                raise RuntimeError("Unable to get CRS from the dataset")
        else:
            logger.critical("Dataset has no CRS defined")
            raise RuntimeError("Missing CRS")

        if epsg != TILE_EPSG: #Web Mercator
            logger.info(f"Reprojecting dataset from EPSG:{epsg} to EPSG:{TILE_EPSG}")
            gdf = gdf.to_crs(epsg=TILE_EPSG)
        else:
            logger.debug(f"Dataset already in EPSG:{TILE_EPSG}")

        self.original_epsg = epsg
        self.current_epsg = TILE_EPSG
        self.source = gdf
        self.source_path = source_path
        logger.info(f"GeoDataset initialized successfully: {len(gdf)} features")
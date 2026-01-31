from pathlib import Path
from box import Box
from typing import Union

class GeoDataset:

    @property
    def bbox(self):
        minx, miny, maxx, maxy = self.source.total_bounds
        bbox_dict = Box({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
        return bbox_dict
    
    @property
    def shape(self):
        return self.source.geometry
    
    def buffer(self, distance:int) -> None:
        self.source.geometry.buffer(distance)

    def __init__(self, source_path: Union[Path, str]):
        import geopandas as gpd
        from pyproj import CRS

        source_path = Path(source_path)
        gdf = gpd.read_file(source_path)
        epsg = None

        if gdf.crs is not None:
            try:
                epsg = CRS.from_user_input(gdf.crs).to_epsg()
            except Exception:
                raise RuntimeError("Unable to get CRS from the dataset")
        else:
            raise RuntimeError("Missing CRS")

        if epsg != 4326:
            gdf = gdf.to_crs(epsg=4326)

        self.original_epsg = epsg
        self.current_epsg = 4326
        self.source = gdf
        self.source_path = source_path

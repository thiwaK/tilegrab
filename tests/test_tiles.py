import unittest
from unittest.mock import Mock
from box import Box
from tilegrab.sources.public import OSM
from tilegrab.tiles import TilesByBBox, TilesByShape
from tilegrab.dataset import GeoDataset
from shapely.geometry import Polygon

class TileTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.mock_ds = Mock(spec=GeoDataset)
        cls.bbox = Box(
            {"minx": -122.5, "miny": 37.7, "maxx": -122.3, "maxy": 37.9}
        )
        cls.shape = [Polygon(
            [(-122.4, 37.8), (-122.4, 37.85), (-122.35, 37.85), (-122.35, 37.8), (-122.4, 37.8)]
        )]

        cls.mock_ds.bbox = cls.bbox
        cls.mock_ds.geometry.geometry = cls.shape

    def test_tiles_by_bbox_creation(self):

        osm = OSM()
        tiles = TilesByBBox(
            geo_dataset=self.mock_ds, 
            tile_source=osm, 
            zoom=10)
        assert tiles.zoom == 10
        assert tiles.source_id == osm.id
        assert tiles.geo_dataset is self.mock_ds

    def test_tiles_by_shape_creation(self):
        osm = OSM()
        tiles = TilesByShape(geo_dataset=self.mock_ds, 
            tile_source=osm, 
            zoom=10)
        assert tiles.zoom == 10
        assert tiles.source_id == osm.id
        assert tiles.geo_dataset is self.mock_ds

    def test_tiles_by_bbox_to_list(self):
        osm = OSM()
        tiles = TilesByBBox(
            geo_dataset=self.mock_ds, 
            tile_source=osm, 
            zoom=10)
        tile_list = tiles.to_list
        assert isinstance(tile_list, list)
        assert len(tile_list) > 0
        for tile in tile_list:
            assert tile.index.z
            assert tile.index.x
            assert tile.index.y
            assert tile.index.z == 10
    
    def test_tiles_by_shape_to_list(self):
        osm = OSM()
        tiles = TilesByShape(
            geo_dataset=self.mock_ds, 
            tile_source=osm, 
            zoom=10)
        tile_list = tiles.to_list
        assert isinstance(tile_list, list)

        for tile in tile_list:
            assert tile.index.z
            assert tile.index.x
            assert tile.index.y
            assert tile.index.z == 10
        
    def test_safe_limit_exceeded(self):
        tiles = TilesByBBox(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=5,
            safe_limit=1)
        assert len(tiles) == 1

        tiles = TilesByShape(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=5,
            safe_limit=1)
        assert len(tiles) == 1

    def test_tiles_len(self):
        tiles = TilesByBBox(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)
        assert len(tiles) == len(tiles.to_list)

        tiles = TilesByShape(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)
        assert len(tiles) == len(tiles.to_list)

    def test_tiles_iter(self):
        tiles = TilesByBBox(geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)
        count = 0
        for tile in tiles:
            assert tile.index.z == 10
            count += 1
        assert count == len(tiles)

        tiles = TilesByShape(geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)
        count = 0
        for tile in tiles:
            assert tile.index.z == 10
            count += 1
        assert count == len(tiles)

    def test_need_download_flag(self):
        tiles = TilesByBBox(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)

        for i, t in enumerate(tiles):
            assert t.need_download == True
            tiles[i].need_download = False
        
        for i, t in enumerate(tiles):
            assert t.need_download == False 
        
        tiles = TilesByShape(
            geo_dataset=self.mock_ds, 
            tile_source=OSM(), 
            zoom=10)

        for i, t in enumerate(tiles):
            assert t.need_download == True
            tiles[i].need_download = False
        
        for i, t in enumerate(tiles):
            assert t.need_download == False 

if __name__ == "__main__":
    unittest.main()
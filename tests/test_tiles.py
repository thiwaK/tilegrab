import unittest
from unittest.mock import Mock
from box import Box
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
        cls.shape = Polygon(
            [(-122.4, 37.8), (-122.4, 37.85), (-122.35, 37.85), (-122.35, 37.8), (-122.4, 37.8)]
        )

        cls.mock_ds.bbox = cls.bbox
        cls.mock_ds.shape = cls.shape

    def test_tiles_by_bbox_creation(self):
        tiles = TilesByBBox(self.mock_ds, zoom=10)
        assert tiles.zoom == 10
        assert tiles.feature == self.mock_ds

    def test_tiles_by_shape_creation(self):
        tiles = TilesByShape(self.mock_ds, zoom=10)
        assert tiles.zoom == 10
        assert tiles.feature == self.mock_ds

    def test_tiles_by_bbox_to_list(self):
        tiles = TilesByBBox(self.mock_ds, zoom=10)
        tile_list = tiles.to_list
        assert isinstance(tile_list, list)
        assert len(tile_list) > 0
        for tile in tile_list:
            assert tile.z
            assert tile.x
            assert tile.y
            assert tile.z == 10
    
    def test_tiles_by_shape_to_list(self):
        tiles = TilesByShape(self.mock_ds, zoom=10)
        tile_list = tiles.to_list
        assert isinstance(tile_list, list)
        # Depending on the shape, might have tiles or not
        for tile in tile_list:
            assert tile.z
            assert tile.x
            assert tile.y
            assert tile.z == 10

    def test_safe_limit_exceeded(self):
        mock_ds = Mock(spec=GeoDataset)
        mock_ds.bbox = Box({"minx": -180, "miny": -90, "maxx": 180, "maxy": 90})
        self.assertRaises(
            ValueError, TilesByBBox, mock_ds, zoom=5, SAFE_LIMIT=1)

    def test_tiles_len(self):
        tiles = TilesByBBox(self.mock_ds, zoom=10)
        assert len(tiles) == len(tiles.to_list)

    def test_tiles_iter(self):
        tiles = TilesByBBox(self.mock_ds, zoom=10)
        count = 0
        for z, x, y in tiles:
            assert z == 10
            count += 1
        assert count == len(tiles)


if __name__ == "__main__":
    unittest.main()
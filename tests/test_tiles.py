import pytest
from unittest.mock import Mock
from box import Box
from tilegrab.tiles import TilesByBBox, TilesByShape
from tilegrab.dataset import GeoDataset


@pytest.fixture
def mock_geodataset_bbox():
    """Mock GeoDataset for bbox-based tiles."""
    mock_ds = Mock(spec=GeoDataset)
    mock_ds.bbox = Box({"minx": -122.5, "miny": 37.7, "maxx": -122.3, "maxy": 37.9})
    return mock_ds

@pytest.fixture
def mock_geodataset_shape():
    """Mock GeoDataset for shape-based tiles."""
    from shapely.geometry import Polygon
    mock_ds = Mock(spec=GeoDataset)
    mock_ds.bbox = Box({"minx": -122.5, "miny": 37.7, "maxx": -122.3, "maxy": 37.9})
    mock_ds.shape = Polygon([(-122.4, 37.8), (-122.4, 37.85), (-122.35, 37.85), (-122.35, 37.8), (-122.4, 37.8)])
    return mock_ds


def test_tiles_by_bbox_creation(mock_geodataset_bbox):
    tiles = TilesByBBox(mock_geodataset_bbox, zoom=10)
    assert tiles.zoom == 10
    assert tiles.feature == mock_geodataset_bbox

def test_tiles_by_shape_creation(mock_geodataset_shape):
    tiles = TilesByShape(mock_geodataset_shape, zoom=10)
    assert tiles.zoom == 10
    assert tiles.feature == mock_geodataset_shape

def test_tiles_by_bbox_to_list(mock_geodataset_bbox):
    tiles = TilesByBBox(mock_geodataset_bbox, zoom=10)
    tile_list = tiles.to_list
    assert isinstance(tile_list, list)
    assert len(tile_list) > 0
    for tile in tile_list:
        assert tile.z
        assert tile.x
        assert tile.y
        assert tile.z == 10

def test_tiles_by_shape_to_list(mock_geodataset_shape):
    tiles = TilesByShape(mock_geodataset_shape, zoom=10)
    tile_list = tiles.to_list
    assert isinstance(tile_list, list)
    # Depending on the shape, might have tiles or not
    for tile in tile_list:
        assert tile.z
        assert tile.x
        assert tile.y
        assert tile.z == 10

def test_safe_limit_exceeded():
    # Mock a large bbox to exceed limit
    mock_ds = Mock(spec=GeoDataset)
    mock_ds.bbox = Box({"minx": -180, "miny": -90, "maxx": 180, "maxy": 90})  # World bbox
    with pytest.raises(ValueError, match="Your query excedes the hard limit.*"):
        tiles = TilesByBBox(mock_ds, zoom=5, SAFE_LIMIT=1) 

def test_tiles_len(mock_geodataset_bbox):
    tiles = TilesByBBox(mock_geodataset_bbox, zoom=10)
    assert len(tiles) == len(tiles.to_list)

def test_tiles_iter(mock_geodataset_bbox):
    tiles = TilesByBBox(mock_geodataset_bbox, zoom=10)
    count = 0
    for z, x, y in tiles:
        assert z == 10
        count += 1
    assert count == len(tiles)



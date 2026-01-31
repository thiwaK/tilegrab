import pytest
from pathlib import Path, WindowsPath, PosixPath
from PIL import Image
from tilegrab.mosaic import Mosaic
from tilegrab.tiles import TilesByBBox
from unittest.mock import Mock
import os

@pytest.fixture
def temp_tiles_dir(tmp_path):
    """Create a temporary directory with fake tile images."""
    tiles_dir = tmp_path / "tiles"
    tiles_dir.mkdir()

    # Create fake images
    img = Image.new("RGB", (256, 256), color="red")
    img.save(tiles_dir / "10_1_2.png")
    img = Image.new("RGB", (256, 256), color="green")
    img.save(tiles_dir / "10_1_3.png")

    return tiles_dir

@pytest.fixture
def mock_tiles():
    mock_tiles = Mock(spec=TilesByBBox)
    mock_tiles.MIN_X = 1
    mock_tiles.MAX_X = 1
    mock_tiles.MIN_Y = 2
    mock_tiles.MAX_Y = 3
    return mock_tiles


def test_mosaic_init(temp_tiles_dir):
    mosaic = Mosaic(directory=str(temp_tiles_dir))

    print("image_col", mosaic.image_col)
    assert all([type(i) == WindowsPath or PosixPath for i in mosaic.image_col])
    assert all([i.exists for i in mosaic.image_col])

    
    # print("image_data", mosaic.image_data)
    assert len(mosaic.image_col) == 2  # Two images


def test_mosaic_merge(temp_tiles_dir, mock_tiles):
    mosaic = Mosaic(directory=str(temp_tiles_dir))
    mosaic.merge(mock_tiles, tile_size=256)

    # Check if output file exists
    assert temp_tiles_dir.exists()

    # Optionally, check image properties
    merged_img = Image.open("merged_output.png")
    assert merged_img.size == (256, 512)  # Based on min/max
import pytest
from pathlib import Path
from PIL import Image
from tilegrab.mosaic import Mosaic
from tilegrab.tiles import TilesByBBox
from unittest.mock import Mock


@pytest.fixture
def temp_tiles_dir(tmp_path):
    """Create a temporary directory with fake tile images."""
    tiles_dir = tmp_path / "tiles"
    tiles_dir.mkdir()

    # Create fake images
    img = Image.new("RGB", (256, 256), color="red")
    img.save(tiles_dir / "10_1_2.png")
    img.save(tiles_dir / "10_1_3.png")

    return 



@pytest.fixture
def mock_tiles():
    mock_tiles = Mock()
    mock_tiles.MIN_X = 1
    mock_tiles.MAX_X = 1
    mock_tiles.MIN_Y = 2
    mock_tiles.MAX_Y = 3
    return mock_tiles


def test_mosaic_init(temp_tiles_dir):
    mosaic = Mosaic(directory=str(temp_tiles_dir))
    assert len(mosaic.image_data) == 2  # Two images


def test_mosaic_merge(temp_tiles_dir, mock_tiles, tmp_path):
    mosaic = Mosaic(directory=str(temp_tiles_dir))
    output_path = tmp_path / "output.png"
    mosaic.merge(mock_tiles, tile_size=256)

    # Check if output file exists
    assert output_path.exists()
    # Optionally, check image properties
    merged_img = Image.open(output_path)
    assert merged_img.size == (256, 512)  # Based on min/max
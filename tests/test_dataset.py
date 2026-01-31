import pytest
from unittest.mock import Mock, patch
from box import Box
from tilegrab.dataset import GeoDataset
from pathlib import Path
import os

# DATA_PATH = r"tests\data\T.geojson"
# assert os.path.isfile(DATA_PATH)

@patch('geopandas.read_file')
@patch('pyproj.CRS.from_user_input')
def test_geodataset_init_with_crs(mock_crs, mock_read):
    mock_gdf = Mock()
    mock_gdf.crs = "EPSG:4326"
    mock_read.return_value = mock_gdf

    mock_crs_instance = Mock()
    mock_crs_instance.to_epsg.return_value = 4326
    mock_crs.return_value = mock_crs_instance

    ds = GeoDataset("test.shp")
    assert ds.source == mock_gdf
    assert ds.source_path == Path("test.shp")


@patch('geopandas.read_file')
def test_geodataset_init_no_crs(mock_read):
    mock_gdf = Mock()
    mock_gdf.crs = None
    mock_read.return_value = mock_gdf

    with pytest.raises(RuntimeError, match="Missing CRS"):
        GeoDataset("test.shp")


@patch('geopandas.read_file')
@patch('pyproj.CRS.from_user_input')
def test_geodataset_init_wrong_crs(mock_crs, mock_read):
    mock_gdf = Mock()
    mock_gdf.crs = "EPSG:3857"
    mock_read.return_value = mock_gdf

    mock_crs_instance = Mock()
    mock_crs_instance.to_epsg.return_value = 3857
    mock_crs.return_value = mock_crs_instance

    with patch.object(mock_gdf, 'to_crs') as mock_to_crs:
        ds = GeoDataset("test.shp")
        mock_to_crs.assert_called_once_with(epsg=4326)


def test_geodataset_bbox():
    mock_ds = Mock()
    mock_ds.source.total_bounds = [1, 2, 3, 4]
    ds = GeoDataset.__new__(GeoDataset)  # Skip init
    ds.source = mock_ds.source
    bbox = ds.bbox
    assert bbox.minx == 1
    assert bbox.miny == 2
    assert bbox.maxx == 3
    assert bbox.maxy == 4


def test_geodataset_shape():
    mock_ds = Mock()
    mock_ds.source.geometry = "fake_geometry"
    ds = GeoDataset.__new__(GeoDataset)
    ds.source = mock_ds.source
    assert ds.shape == "fake_geometry"
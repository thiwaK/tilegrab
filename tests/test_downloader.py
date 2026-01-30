import pytest
from unittest.mock import Mock, patch
from tilegrab.downloader import Downloader
from tilegrab.sources import OSM
from tilegrab.tiles import TilesByBBox


@pytest.fixture
def mock_tiles():
    mock_tiles = Mock()
    mock_tiles.to_list = [Mock(z=10, x=1, y=2), Mock(z=10, x=1, y=3)]
    mock_tiles.__len__ = Mock(return_value=2)
    return mock_tiles


@pytest.fixture
def downloader(mock_tiles):
    source = OSM()
    return Downloader(tiles=mock_tiles, tile_source=source, output_dir="test_tiles")


@patch('tilegrab.downloader.requests.Session.get')
def test_download_tile_success(mock_get, downloader):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.headers = {"content-type": "image/png"}
    mock_response.content = b"fake image data"
    mock_get.return_value = mock_response

    with patch.object(downloader, '_save') as mock_save:
        path, success = downloader.download_tile(10, 1, 2)
        assert success
        assert "10_1_2.png" in path
        mock_save.assert_called_once()


@patch('tilegrab.downloader.requests.Session.get')
def test_download_tile_failure(mock_get, downloader):
    mock_get.side_effect = Exception("Network error")

    with pytest.raises(RuntimeWarning, match="Failed to fetch"):
        downloader.download_tile(10, 1, 2)


@patch('tilegrab.downloader.requests.Session.get')
@patch('concurrent.futures.ThreadPoolExecutor')
def test_run_download(mock_executor, mock_get, downloader, mock_tiles):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.headers = {"content-type": "image/png"}
    mock_response.content = b"data"
    mock_get.return_value = mock_response

    mock_future = Mock()
    mock_future.result.return_value = ("path", True)
    mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
    mock_executor.return_value.__enter__.return_value.map.return_value = [mock_future]

    with patch.object(downloader, '_save'):
        results = downloader.run(workers=1, show_progress=False)
        assert isinstance(results, dict)
        assert len(results) == 2  # Two tiles
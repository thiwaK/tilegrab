from pathlib import Path
import unittest
from unittest.mock import Mock, MagicMock, patch
from tempfile import TemporaryDirectory
from PIL import Image
from io import BytesIO

from tilegrab.dataset import Coordinate, GeoDataset
from tilegrab.downloader.runner import Downloader
import tilegrab.downloader.worker as worker

from tilegrab.downloader.config import DownloadConfig
from tilegrab.downloader.session import create_session
from tilegrab.downloader.status import DownloadStatus
from tilegrab.downloader.worker import download_tile
from tilegrab.images.collection import TileImageCollection
from tilegrab.images.image import TileImage
from tilegrab.sources import OSM
from tilegrab.tiles import TilesByBBox, Tile, TileCollection
from requests import Session

from tilegrab.tiles.tile import TileIndex


class DownloaderTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.osm = Mock(spec=OSM)

        tile1 = Tile(z=10, x=1, y=2, source=OSM())
        tile1.need_download = True
        cls.tile1 = tile1

        tile2 = Tile(z=10, x=1, y=3, source=OSM())
        tile2.need_download = False
        cls.tile2 = tile2

        geodataset = MagicMock(spec=GeoDataset)
        geodataset.bbox = Coordinate(1, 2, 1, 3)

        tiles = [tile1, tile2]
        cls.tiles_by_bbox:TilesByBBox = MagicMock(spec=TilesByBBox)
        cls.tiles_by_bbox.to_list = tiles
        cls.tiles_by_bbox._tile_count = 2
        cls.tiles_by_bbox.__len__.return_value = 2
        cls.tiles_by_bbox.__iter__.return_value = iter(tiles)
        cls.tiles_by_bbox.__getitem__.side_effect = tiles.__getitem__
        cls.tiles_by_bbox.MIN_X = 1
        cls.tiles_by_bbox.MAX_X = 1
        cls.tiles_by_bbox.MIN_Y = 2
        cls.tiles_by_bbox.MAX_Y = 3
        cls.tiles_by_bbox.source_id = "osm"
        cls.tiles_by_bbox.source_name = "OSM"
        cls.tiles_by_bbox.geo_dataset = geodataset
        cls.tiles_by_bbox.tiles_in_bound.return_value = iter(tiles)
        cls.tiles_by_bbox.build_tile_cache.return_value = tiles
        cls.tiles_by_bbox._cache = tiles

        cls.dl_cfg = DownloadConfig(
        timeout=15, max_retries=5, backoff_factor=0.3, overwrite=True)

    def setup_mock_response(self):
        patcher = patch.object(Session, "get")
        self.addCleanup(patcher.stop)
        self.mock_get = patcher.start()

        self.response = MagicMock()
        self.response.status_code = 200
        self.response.raise_for_status.return_value = None
        self.response.headers = {"content-type": "image/png"}

        buf = BytesIO()
        Image.new("RGB", (256, 256), color="red").save(buf, format="PNG")
        buf.seek(0)
        png_bytes = buf.read()
        self.response.iter_content.return_value = [png_bytes]
        self.response.content = png_bytes

        self.mock_get.return_value = self.response
    
    def setup_mock_download_tile(self):
        patcher = patch("tilegrab.downloader.worker.download_tile")
        self.addCleanup(patcher.stop)
        self.mock_download_tile = patcher.start()

        download_result = MagicMock()
        download_result.tile = self.tile1
        download_result.status = DownloadStatus.SUCCESS
        download_result.result = MagicMock()
        download_result.url = self.tile1.url

        self.mock_download_tile.return_value = download_result
        
    def test_mock_download_tile(self):

        self.setup_mock_download_tile()

        session = create_session(self.dl_cfg)
        worker.download_tile(
            tile=self.tile1,
            session=session,
            timeout=0.5)
        
        self.mock_download_tile.assert_called_once()

    def test_download_tile(self):
        
        self.setup_mock_response()
        self.setup_mock_download_tile()

        session = create_session(self.dl_cfg)
        worker.download_tile(
            tile=self.tile1, session=session, timeout=15)

        self.mock_download_tile.assert_called_once()

    def test_download_tile_success(self):
        
        self.setup_mock_response()

        session = create_session(self.dl_cfg)
        dl_res = download_tile(tile=self.tile1, session=session, timeout=15)

        self.mock_get.assert_called_once_with(
            self.tile1.url,
            timeout=15,
        )

        assert dl_res.url == self.tile1.url
        assert dl_res.status == DownloadStatus.SUCCESS
        assert dl_res.tile is self.tile1
        assert dl_res.result != None
    
    def test_download_tile_skip(self):
        
        self.setup_mock_response()

        session = create_session(self.dl_cfg)
        dl_res = download_tile(tile=self.tile2, session=session, timeout=15)

        self.mock_get.assert_not_called()

        assert dl_res.url == self.tile2.url
        assert dl_res.status == DownloadStatus.SKIP
        assert dl_res.tile is self.tile2
        assert dl_res.result == None

    def test_download_config(self):
        dl_cfg = DownloadConfig()
        assert hasattr(dl_cfg, "backoff_factor")
        assert hasattr(dl_cfg, "max_retries")
        assert hasattr(dl_cfg, "overwrite")
        assert hasattr(dl_cfg, "timeout")

    def test_downloader_instantiation(self):

        assert len(self.tiles_by_bbox) == 2
        assert self.tiles_by_bbox[0] is self.tile1

        with TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)

            dl = Downloader(
                tile_collection=self.tiles_by_bbox,
                config=self.dl_cfg,
                tile_dir=temp_dir
            )
            assert dl.config is self.dl_cfg
            assert dl.tile_dir is temp_dir

    def test_downloader_run(self):
        
        self.setup_mock_response()

        assert any([i.need_download for i in self.tiles_by_bbox])
        
        with TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)

            dl = Downloader(
                tile_collection=self.tiles_by_bbox,
                config=self.dl_cfg,
                tile_dir=temp_dir,
                resume = False
            )
            tileImageCol = dl.run(parallel_download=False, show_progress=False)
            self.mock_download_tile.assert_called_once()
            self.mock_get.assert_called_once()
            
            assert type(tileImageCol) is TileImageCollection
    
    def _test_downloader_run_result(self):
        
        self.setup_mock_response()
        self.setup_mock_download_tile()

        with TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)

            dl = Downloader(
                tile_collection=self.tiles_by_bbox,
                config=self.dl_cfg,
                tile_dir=temp_dir,
                resume = False
            )
            tileImageCol = dl.run(show_progress=False, parallel_download=False)
            
            
            self.mock_download_tile.assert_called_once()
            self.mock_get.assert_called_once()
            
            count = 0
            for t in tileImageCol:
                assert t.image == b"fake image data"
                count += 1
            
            assert count == 2

if __name__ == "__main__":
    unittest.main()
    
import unittest
from unittest.mock import Mock, MagicMock, patch
from tilegrab.downloader import Downloader
from tilegrab.sources import OSM
from tilegrab.tiles import TilesByBBox, Tile, TileCollection
from requests import Session

class DownloaderTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.osm = Mock(spec=OSM)
        cls.tiles_by_bbox = Mock(spec=TilesByBBox)
        cls.tiles_by_bbox.to_list = [Mock(z=10, x=1, y=2), Mock(z=10, x=1, y=3)]
        cls.tiles_by_bbox.__len__ = Mock(return_value=2)
    
    # @property
    # def downloader(self):
    #     return Downloader(
    #         tile_collection=self.tiles_by_bbox, 
    #         temp_tile_dir="test_tiles"
    #     )
        
    # @patch.object(Session, 'get')
    # def test_download_run(self, mock_get):
    #     mock_response = MagicMock()
    #     mock_response.status_code = 200
    #     mock_response.raise_for_status.return_value = None
    #     mock_response.headers = {"content-type": "image/png"}
    #     mock_response.content = b"fake image data"
    #     mock_get.return_value = mock_response
    #     self.downloader.run()


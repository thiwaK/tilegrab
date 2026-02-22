import unittest
from tilegrab.sources import OSM, GoogleSat, ESRIWorldImagery, Nearmap
from tilegrab.sources import TileSource
from utils.attr_utils import has_attr_path

class TileSourceTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.t_sources:list[TileSource] = [
            OSM(), GoogleSat(), ESRIWorldImagery(), Nearmap(api_key="TESTKEY")
        ]

    PROPERTY_ARR = {
        "name", "description", "url_template", "uid"
    }

    def test_property_arr_attributes_exist(self):
        for attr in self.PROPERTY_ARR:
            for source in self.t_sources:
                self.assertTrue(
                    has_attr_path(source, attr),
                    f"No attribute path `{attr}` on TileSource {source.name}"
                )
                assert getattr(source, attr) != ""
    
    def test_source_url_generation(self):
        for source in self.t_sources:
            url = source.get_url(1,1,1)

            assert url.startswith("https://") or url.startswith("http://"), f"Invalid url generation {source.name}. {url}"

            assert url.count("/1/1/1") == 1 or url.count("&x=1&y=1&z=1") == 1, f"Invalid url generation {source.name}. {url}"

if __name__ == "__main__":
    unittest.main()
from pathlib import Path
from tilegrab.dataset import GeoDataset
import unittest
from utils.attr_utils import get_attr_by_path, has_attr_path, normalize_expected

DATA_PATH = Path("tests/data/T.geojson")
assert DATA_PATH.is_file(), "Missing test dataset"

class GeoDatasetTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.geodata = GeoDataset(str(DATA_PATH))

    PROPERTY_MAP = {
        "shape.name": "geometry",
        "shape.crs.name": "WGS 84",
        "bbox.minx": 80.59111369868114,   # numeric
        "bbox.maxy": 7.267703227740259,   # numeric
        "original_epsg": 3857,
        "current_epsg": 4326,
        "source_path": DATA_PATH.resolve()
    }

    def test_property_map_attributes_exist(self):
        for path in self.PROPERTY_MAP.keys():
            self.assertTrue(
                has_attr_path(self.geodata, path),
                f"No attribute path `{path}` on GeoDataset"
            )

    def test_property_map_values(self):
        for path, expected in self.PROPERTY_MAP.items():
            actual = get_attr_by_path(self.geodata, path)
            expected_norm = normalize_expected(expected)
            if isinstance(expected_norm, Path):
                self.assertEqual(Path(actual).resolve(), expected_norm.resolve(), f"{path} -> {actual!r} != {expected_norm!r}")

            elif isinstance(expected_norm, float):
                self.assertAlmostEqual(actual, expected_norm, places=9, msg=f"{path} -> {actual!r} != {expected_norm!r}")

            else:
                self.assertEqual(actual, expected_norm, f"{path} -> {actual!r} != {expected_norm!r}")

if __name__ == "__main__":
    unittest.main()
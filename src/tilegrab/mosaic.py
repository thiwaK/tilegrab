from dataclasses import dataclass
from pathlib import Path
from typing import List
from PIL import Image
import re
import os

from tilegrab.tiles import TileCollection


class Mosaic:

    def __init__(
        self, directory: str = "saved_tiles", ext: str = ".png", recursive: bool = False
    ):
        self.directory = directory
        self.ext = ext
        self.recursive = recursive

        self.image_col = self._get_images()
        assert len(self.image_col) > 0

        pat = re.compile(
            r"^([0-9]+)_([0-9]+)_([0-9]+)\.[A-Za-z0-9]+$"
        )
        self.image_data = {}

        for i in self.image_col:
            m = pat.match(os.path.basename(str(i)))
            if m:
                first = m.group(1)
                second = m.group(2)
                third = m.group(3)

                self.image_data[i] = [int(second), int(third), int(first)]

        assert len(self.image_data.keys()) > 0

        print(f"Processing {len(self.image_data.keys())} tiles...")

    def _get_images(self) -> List[Path]:

        directory = Path(self.directory)
        ext = self.ext

        if not ext.startswith("."):
            ext = "." + self.ext

        if self.recursive:
            return [p for p in directory.rglob(f"*{ext}") if p.is_file()]
        else:
            return [p for p in directory.glob(f"*{ext}") if p.is_file()]

    def merge(self, tiles: TileCollection, tile_size: int = 256):

        img_w = int((tiles.MAX_X - tiles.MIN_X + 1) * tile_size)
        img_h = int((tiles.MAX_Y - tiles.MIN_Y + 1) * tile_size)
        print(f"Image size: {img_w}x{img_h}")

        merged_image = Image.new("RGB", (img_w, img_h))

        for img_path, img_id in self.image_data.items():
            x, y, _ = img_id

            print(x - tiles.MIN_X + 1, "x" ,y - tiles.MIN_Y + 1)

            img = Image.open(img_path)
            img.load()

            px = int((x - tiles.MIN_X) * tile_size)
            py = int((y - tiles.MIN_Y) * tile_size)

            merged_image.paste(img, (px, py))

        merged_image.save(os.path.join(self.directory, "merged_output.png"))

from dataclasses import dataclass
from pathlib import Path
from typing import List
from PIL import Image, ImageFile
import numpy as np
import re

from Core import Tiles

@dataclass
class Moasic:
    directory: Path | str = "saved_tiles"
    ext: str = ".png"
    recursive: bool = False

    def __init__(self):
        pat = re.compile(r'^[A-Za-z0-9]+_[A-Za-z0-9]+\\([1-9]+)_([0-9]+)_([0-9]+)\.[A-Za-z0-9]+$')
        self.image_col = self._get_images()
        image_data = {}

        for i in self.image_col:
            m = pat.match(str(i))
            if m:
                first = m.group(1)
                second = m.group(2)
                third = m.group(3)

                image_data[i] = [int(second), int(third), int(first)]
        
        self.image_data = image_data
        
    def _get_images(self) -> List[Path]:
        
        directory = Path(self.directory)
        ext = self.ext

        if not ext.startswith('.'):
            ext = '.' + self.ext

        if self.recursive:
            return [p for p in directory.rglob(f"*{ext}") if p.is_file()]
        else:
            return [p for p in directory.glob(f"*{ext}") if p.is_file()]
    
    def merge(self, tiles:Tiles, tile_size=256):
        
        max_x = [t.x  for t in tiles.to_list]
        max_y = [t.y  for t in tiles.to_list]
        max_x, min_x = max(max_x), min(max_x)
        max_y, min_y = max(max_y), min(max_y)
        
        img_w = int((max_x - min_x + 1) * tile_size)
        img_h = int((max_y - min_y + 1) * tile_size)
        print(f"Image size: {img_w}x{img_h}")

        merged_image = Image.new(
            "RGB", (img_w, img_h)
        )
        

        for img_path, img_id in self.image_data.items():
            x, y ,_ = img_id

            # print(x - min_x + 1, "x" ,y - min_y + 1)

            img = Image.open(img_path)
            img.load()

            px = int((x - min_x) * tile_size)
            py = int((y - min_y) * tile_size)

            merged_image.paste(img, (px, py))
        
        merged_image.save("merged_output.png")

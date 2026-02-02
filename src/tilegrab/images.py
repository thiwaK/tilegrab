from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, List, Optional, Tuple, Union
from PIL import Image as PLIImage
from box import Box
from tilegrab.tiles import Tile, TileCollection
import os


class ExportType:
    PNG: int = 1
    JPG: int = 2
    TIFF: int = 3

@dataclass
class TileImage:
    width: int = 256
    height: int = 256

    def __init__(self, tile: Tile, image: Union[bytes, bytearray]) -> None:
        self._tile = tile
        self._img = PLIImage.open(BytesIO(image))
        self._path: Union[Path, None] = None
        self._ext: str = self._get_image_type(image)

    def __repr__(self) -> str:
        return f"TileImage; name={self.name}; path={self.path}; url={self.url}; position={self.position}"

    def _get_image_type(self, data: Union[bytes, bytearray]) -> str:

        b = bytes(data)

        # PNG: 8 bytes
        if b.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'

        # JPEG / JPG: files start with FF D8 and end with FF D9; common check uses start bytes
        if len(b) >= 2 and b[0:2] == b'\xff\xd8':
            return 'jpg'  # treat both jpg and jpeg as 'jpg'

        # BMP: starts with 'BM' (0x42 0x4D)
        if len(b) >= 2 and b[0:2] == b'BM':
            return 'bmp'

        return "png"
    
    def save(self):
        self._img.save(self.path)

    @property
    def name(self) -> str:
        return f"{self._tile.z}_{self._tile.x}_{self._tile.y}.{self._ext}"
    
    @property
    def tile(self) -> Tile:
        return self._tile
    
    @property
    def image(self) -> PLIImage.Image:
        self._img.load()
        return self._img
    
    @property
    def path(self) -> Path:
        if self._path is None:
            raise RuntimeError("Image is not attached to a collection")
        return self._path

    @path.setter
    def path(self, value: Any):
        if isinstance(value, Path):
            self._path = value
            return

        elif isinstance(value, str):
            self._path = Path(value)
            return

        elif isinstance(value, WindowsPath):
            self._path = Path(value)
            return

        elif isinstance(value, PosixPath):
            self._path = Path(value)
            return

        raise TypeError(
            "value must be a Path, WindowsPath, PosixPath, or path-like str"
        )

    @property
    def extension(self) -> str:
        if self._ext is None:
            raise RuntimeError("Image does not have an extension")
        return self._ext

    @extension.setter
    def extension(self, val: str):
        self._ext = val

    @property
    def position(self) -> Box:
        return self._tile.position

    @property
    def url(self) -> Union[str, None]:
        return self._tile.url


class TileImageCollection:
    images: List[TileImage] = []
    width:int = 0
    height:int = 0

    def append(self, img: TileImage):
        img.path = os.path.join(self.path, img.name)
        self.images.append(img)
        img.save()

    def __init__(self, path: Union[Path, str]) -> None:
        self.path = Path(path)

        # print(f"ImageCollection is at", path)

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for i in self.images:
            yield i

    def __repr__(self) -> str:
        return f"ImageCollection; len={len(self)}"

    def _update_collection_dim(self):
        x = [img.tile.x for img in self.images]
        y = [img.tile.y for img in self.images]
        minx, maxx = min(x), max(x)
        miny, maxy = min(y), max(y)

        self.width = int(
            (maxx - minx + 1) * self.images[0].width
        )
        self.height = int(
            (maxy - miny + 1) * self.images[0].height
        )

    def mosaic(self):

        self._update_collection_dim()
        print(self)

        print(f"Image size: {self.width}x{self.height}")
        merged_image = PLIImage.new("RGB", (self.width, self.height))

        for image in self.images:
            print(image.position.x + 1, 'x' , image.position.y + 1)
            px = int((image.position.x) * image.width)
            py = int((image.position.y) * image.height)

            merged_image.paste(image.image, (px, py))

        merged_image.save("merged_output.png")

    def export_collection(self, type: ExportType):
        pass

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, List, Optional, Tuple, Union
from PIL import Image as PLIImage
from box import Box
from tilegrab.tiles import Tile, TileCollection
import os

logger = logging.getLogger(__name__)

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
        try:
            self._img = PLIImage.open(BytesIO(image))
            logger.debug(f"TileImage created for z={tile.z},x={tile.x},y={tile.y}")
        except Exception as e:
            logger.error(f"Failed to open image for tile z={tile.z},x={tile.x},y={tile.y}", exc_info=True)
            raise
        
        self._path: Union[Path, None] = None
        self._ext: str = self._get_image_type(image)

    def __repr__(self) -> str:
        return f"TileImage; name={self.name}; path={self.path}; url={self.url}; position={self.position}"

    def _get_image_type(self, data: Union[bytes, bytearray]) -> str:
        b = bytes(data)

        # PNG: 8 bytes
        if b.startswith(b'\x89PNG\r\n\x1a\n'):
            logger.debug(f"Image detected as PNG")
            return 'png'

        # JPEG / JPG: files start with FF D8 and end with FF D9
        if len(b) >= 2 and b[0:2] == b'\xff\xd8':
            logger.debug(f"Image detected as JPG")
            return 'jpg'

        # BMP: starts with 'BM' (0x42 0x4D)
        if len(b) >= 2 and b[0:2] == b'BM':
            logger.debug(f"Image detected as BMP")
            return 'bmp'

        logger.warning(f"Unknown image format, defaulting to PNG")
        return "png"
    
    def save(self):
        try:
            self._img.save(self.path)
            logger.debug(f"Image saved to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save image to {self.path}", exc_info=True)
            raise

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
            logger.error(f"Attempting to access path for unattached image")
            raise RuntimeError("Image is not attached to a collection")
        return self._path

    @path.setter
    def path(self, value: Any):
        if isinstance(value, Path):
            self._path = value
            logger.debug(f"Image path set to {value}")
            return

        elif isinstance(value, str):
            self._path = Path(value)
            logger.debug(f"Image path set to {value}")
            return

        elif isinstance(value, WindowsPath):
            self._path = Path(value)
            logger.debug(f"Image path set to {value}")
            return

        elif isinstance(value, PosixPath):
            self._path = Path(value)
            logger.debug(f"Image path set to {value}")
            return

        logger.error(f"Invalid path type: {type(value)}")
        raise TypeError(
            "value must be a Path, WindowsPath, PosixPath, or path-like str"
        )

    @property
    def extension(self) -> str:
        if self._ext is None:
            logger.error("Accessing extension for image without extension")
            raise RuntimeError("Image does not have an extension")
        return self._ext

    @extension.setter
    def extension(self, val: str):
        self._ext = val
        logger.debug(f"Image extension set to {val}")

    @property
    def position(self) -> Box:
        return self._tile.position

    @property
    def url(self) -> Union[str, None]:
        return self._tile.url


class TileImageCollection:
    images: List[TileImage] = []
    width: int = 0
    height: int = 0

    def append(self, img: TileImage):
        img.path = os.path.join(self.path, img.name)
        self.images.append(img)
        logger.debug(f"Image appended to collection: {img.name}")
        img.save()

    def __init__(self, path: Union[Path, str]) -> None:
        self.path = Path(path)
        logger.info(f"TileImageCollection initialized at {self.path}")

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for i in self.images:
            yield i

    def __repr__(self) -> str:
        return f"ImageCollection; len={len(self)}"

    def _update_collection_dim(self):
        if not self.images:
            logger.warning("Attempting to update collection dimensions with no images")
            return
        
        x = [img.tile.x for img in self.images]
        y = [img.tile.y for img in self.images]
        minx, maxx = min(x), max(x)
        miny, maxy = min(y), max(y)

        self.width = int((maxx - minx + 1) * self.images[0].width)
        self.height = int((maxy - miny + 1) * self.images[0].height)
        logger.info(f"Collection dimensions calculated: {self.width}x{self.height}")

    def mosaic(self):
        logger.info("Starting mosaic creation")
        self._update_collection_dim()

        logger.info(f"Mosaicking {len(self.images)} images into {self.width}x{self.height}")
        merged_image = PLIImage.new("RGB", (self.width, self.height))

        for image in self.images:
            px = int((image.position.x) * image.width)
            py = int((image.position.y) * image.height)
            logger.debug(f"Pasting image at position ({px}, {py}): {image.name}")
            merged_image.paste(image.image, (px, py))

        output_path = "merged_output.png"
        merged_image.save(output_path)
        logger.info(f"Mosaic saved to {output_path}")

    def export_collection(self, type: ExportType):
        logger.info(f"Exporting collection as type {type}")
        pass
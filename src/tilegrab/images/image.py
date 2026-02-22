import logging
from dataclasses import dataclass
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, Union
from PIL import Image as PILImage
from tilegrab.tiles import Tile, GeoBounds, TileIndex

logger = logging.getLogger(__name__)



@dataclass
class TileImage:
    width: int = 256
    height: int = 256
    

    def __init__(self, tile: Tile, image: Union[bytes, bytearray]) -> None:
        from io import BytesIO

        self._tile = tile
        try:
            self._img = PILImage.open(BytesIO(image))
            logger.debug(
                f"TileImage created for z={tile.index.z},x={tile.index.x},y={tile.index.y}")
        except Exception as e:
            logger.error(
                f"Failed to open image for tile z={tile.index.z},x={tile.index.x},y={tile.index.y}",
                exc_info=True,
            )
            logger.error(e)
            raise

        self._path: Union[Path, None] = None
        self._ext: str = self._get_image_type(image)

    def __repr__(self) -> str:
        return f"TileImage; name={self.name}; path={self.path}; url={self.url}; position={self.index}"

    def _get_image_type(self, data: Union[bytes, bytearray]) -> str:
        b = bytes(data)

        # PNG: 8 bytes
        if b.startswith(b"\x89PNG\r\n\x1a\n"):
            logger.debug(f"Image detected as PNG")
            return "png"

        # JPEG / JPG: files start with FF D8 and end with FF D9
        if len(b) >= 2 and b[0:2] == b"\xff\xd8":
            logger.debug(f"Image detected as JPG")
            return "jpg"

        # BMP: starts with 'BM' (0x42 0x4D)
        if len(b) >= 2 and b[0:2] == b"BM":
            logger.debug(f"Image detected as BMP")
            return "bmp"

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
        return f"{self._tile.index.z}_{self._tile.index.x}_{self._tile.index.y}.{self._ext}"

    @property
    def tile(self) -> Tile:
        return self._tile
    
    @tile.setter
    def tile(self, value:Tile):
        self._tile = value

    @property
    def image(self) -> PILImage.Image:
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
    def bounds(self) -> GeoBounds:
        return self._tile.bounds
    
    @property
    def index(self) -> TileIndex:
        return self._tile.index

    @property
    def url(self) -> Union[str, None]:
        return self._tile.url


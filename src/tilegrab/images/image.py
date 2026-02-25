import io
import logging
from dataclasses import dataclass
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, Union
from PIL import Image as PILImage
from tilegrab.dataset import Coordinate
from tilegrab.tiles import Tile, TileIndex

logger = logging.getLogger(__name__)



@dataclass
class TileImage:
    width: int = 256
    height: int = 256
    format:str = "png"

    def __init__(self, 
            tile: Tile, 
            image: Union[bytes, bytearray]) -> None:
        from io import BytesIO

        assert tile.index.z and tile.index.y and tile.index.x
        self._tile = tile
        try:
            self._img = PILImage.open(BytesIO(image))
            # self._img.load()
            logger.debug(
                f"TileImage created for z={tile.index.z},x={tile.index.x},y={tile.index.y}")
        except Exception as e:
            logger.error(
                f"Failed to open image for tile z={tile.index.z},x={tile.index.x},y={tile.index.y}",
                exc_info=True,
            )
            logger.error(e)
            raise RuntimeError

        self._path: Union[Path, None] = None

    def __repr__(self) -> str:
        return f"TileImage; name={self.name}; path={self.path}; url={self.url}; position={self.index}"

    def save(self):
        try:
            img_location = self.path / self.name
            self._img.save(fp=img_location, format=self.format)
            logger.debug(f"Image saved to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save image to {self.path}", exc_info=True)
            raise

    @property
    def name(self) -> str:
        return f"{self._tile.index.z}_{self._tile.index.x}_{self._tile.index.y}.{self.format}"

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
        return self.format

    @extension.setter
    def extension(self, val: str):
        self.format = val
        logger.debug(f"Image extension set to {val}")

    @property
    def bounds(self) -> Coordinate:
        return self._tile.bounds
    
    @property
    def index(self) -> TileIndex:
        return self._tile.index

    @property
    def url(self) -> Union[str, None]:
        return self._tile.url


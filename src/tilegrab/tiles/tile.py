import logging
from typing import Tuple, Union
from dataclasses import dataclass
from box import Box

logger = logging.getLogger(__name__)

@dataclass
class Tile:
    x: int = 0
    y: int = 0
    z: int = 0

    def __post_init__(self):
        self._position = None
        logger.debug(f"Tile created: x={self.x}, y={self.y}, z={self.z}")

    # @classmethod
    # def from_tuple(cls, t: tuple[int, int, int]) -> "Tile":
    #     logger.debug(f"Creating Tile from tuple: {t}")
    #     return cls(*t)

    @property
    def url(self) -> Union[str, None]:
        return self._url

    @url.setter
    def url(self, value: str):
        logger.debug(f"Tile URL set for z={self.z},x={self.x},y={self.y}")
        self._url = value

    @property
    def position(self) -> Box:
        if self._position is None:
            logger.error(f"Tile position not set: z={self.z}, x={self.x}, y={self.y}")
            raise RuntimeError("Image does not have a position")
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float]):
        x, y = self.x - value[0], self.y - value[1]
        self._position = Box({"x": x, "y": y})
        logger.debug(f"Tile position calculated: x={x}, y={y}")
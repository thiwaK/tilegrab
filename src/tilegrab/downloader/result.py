from dataclasses import dataclass
from typing import Union

from tilegrab.tiles import Tile
from tilegrab.images import TileImage

from .status import DownloadStatus


@dataclass(frozen=True, slots=True)
class DownloadResult:
    tile: Tile
    status: DownloadStatus
    result: Union[TileImage, None]
    url: str

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Union
import requests
from requests.adapters import HTTPAdapter, Retry
from tqdm import tqdm
import tempfile
from pathlib import Path

from tilegrab.sources import TileSource
from tilegrab.tiles import TileCollection, Tile
from tilegrab.images import TileImageCollection, TileImage

logger = logging.getLogger(__name__)

@dataclass
class Downloader:
    tiles: TileCollection
    tile_source: TileSource
    temp_tile_dir: Optional[Union[str, Path]] = None
    session: Optional[requests.Session] = None
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 5
    BACKOFF_FACTOR: int = 0
    OVERWRITE: bool = True

    def __post_init__(self):
        if not self.temp_tile_dir:
            tmpdir = tempfile.mkdtemp()
            self.temp_tile_dir = Path(tmpdir)
            logger.debug(f"Created temporary directory: {tmpdir}")
        else:
            logger.debug(f"Using specified tile directory: {self.temp_tile_dir}")

        os.makedirs(self.temp_tile_dir, exist_ok=True)
        self.session = self.session or self._init_session()
        self.image_col = TileImageCollection(self.temp_tile_dir)
        logger.info(f"Downloader initialized: source={self.tile_source.name}, timeout={self.REQUEST_TIMEOUT}s, max_retries={self.MAX_RETRIES}")

    def _init_session(self) -> requests.Session:
        logger.debug("Initializing HTTP session with retry strategy")
        session = requests.Session()
        retries = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "HEAD"]),
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        return session

    def download_tile(self, tile: Tile) -> bool:
        x, y, z = tile.x, tile.y, tile.z
        url = self.tile_source.get_url(z, x, y)
        headers = self.tile_source.headers() or {}
        tile.url = url

        logger.debug(f"Downloading tile: z={z}, x={x}, y={y}")
        try:
            resp = self.session.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT)  # type: ignore
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image"):
                logger.warning(f"Unexpected content type for z={z},x={x},y={y}: {content_type}")
                raise ValueError(
                    f"Unexpected content type {z}/{x}/{y}: {content_type}"
                )
            
            content = resp.content
            if not content:
                logger.warning(f"Empty content received for tile z={z},x={x},y={y}")
                return False
            
            img = TileImage(tile, content)
            self.image_col.append(img)
            logger.debug(f"Tile downloaded successfully: z={z}, x={x}, y={y}")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch tile z={z},x={x},y={y}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading z={z},x={x},y={y}", exc_info=True)
            return False

    def run(
        self,
        workers: int = 8,   
        show_progress: bool = True,
    ) -> TileImageCollection:
        logger.info(f"Starting download run: {len(self.tiles)} tiles, workers={workers}, show_progress={show_progress}")
        
        results = []

        if show_progress:
            pbar = tqdm(total=len(self.tiles), desc=f"Downloading", unit="tile")
        else:
            pbar = None
        
        for tile in self.tiles.to_list:
            res = self.download_tile(tile)
            results.append(res)
            if pbar:
                pbar.update(1)
        
        # with ThreadPoolExecutor(max_workers=workers) as exe:
        #     future_to_tile = {
        #         exe.submit(self.download_tile, tile): tile for tile in self.tiles.to_list
        #     }
        #     for fut in as_completed(future_to_tile):
        #         try:
        #             results.append(fut.result())
        #         except Exception:
        #             results.append(False)

        #         if pbar:
        #             pbar.update(1)

        if pbar:
            pbar.close()

        self._evaluate_result(results)
        return self.image_col

    def _evaluate_result(self, result: List):
        success = sum(1 for v in result if v)
        total = len(self.tiles)
        logger.info(f"Download completed: {success}/{total} successful ({100*success/total:.1f}%)")
        if success < total:
            logger.warning(f"Failed to download {total - success} tiles")



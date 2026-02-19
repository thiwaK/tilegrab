import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Union
import requests
from pathlib import Path

from tilegrab.tiles import TileCollection, Tile
from tilegrab.images import TileImageCollection, TileImage


logger = logging.getLogger(__name__)

@dataclass
class Downloader:
    tile_collection: TileCollection
    temp_tile_dir: Optional[Union[str, Path]] = None
    session: Optional[requests.Session] = None
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 5
    BACKOFF_FACTOR: int = 0
    OVERWRITE: bool = True

    def __post_init__(self):
        if not self.temp_tile_dir:
            import tempfile
            tmpdir = tempfile.mkdtemp()
            self.temp_tile_dir = Path(tmpdir)
            logger.debug(f"Created temporary directory: {tmpdir}")
        else:
            logger.debug(f"Using specified tile directory: {self.temp_tile_dir}")

        os.makedirs(self.temp_tile_dir, exist_ok=True)
        self.session = self.session or self._init_session()
        self.image_col = TileImageCollection(self.temp_tile_dir)
        logger.info(f"Downloader initialized: tile_count={len(self.tile_collection)}, timeout={self.REQUEST_TIMEOUT}s, max_retries={self.MAX_RETRIES}")

    def _init_session(self) -> requests.Session:
        from requests.adapters import HTTPAdapter, Retry
    
        logger.debug("Initializing HTTP session with retry strategy")
        session = requests.Session()
        
        retries = Retry(
            total=self.MAX_RETRIES,
            connect=self.MAX_RETRIES,
            read=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(("GET", "HEAD")),
            raise_on_status=False,
            redirect=False,
        )

        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=20,
            pool_maxsize=20,
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update({
            "referer": "",
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 QGIS/34202/Windows 11 Version 2009",
            "connection": "Keep-Alive ",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,*",
        })

        return session

    def download_tile(self, tile: Tile) -> bool:
        x, y, z = tile.index.x, tile.index.y, tile.index.z
        url = tile.url

        logger.debug(f"Downloading tile: z={z}, x={x}, y={y}")
        try:
            resp = self.session.get(url, timeout=self.REQUEST_TIMEOUT) # type: ignore
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
            
            img = TileImage(tile=tile, image=content)
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
        workers: Union[int, None] = None,   
        show_progress: bool = True,
        parallel_download: bool = True
    ) -> TileImageCollection:
        logger.info(f"Starting download run: {len(self.tile_collection)} tiles, workers={workers}, show_progress={show_progress}")
        
        results = []

        if show_progress:
            from tqdm import tqdm
            pbar = tqdm(total=len(self.tile_collection), desc=f"      Downloading", unit="tile")
        else:
            pbar = None
        

        if parallel_download:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as exe:
                future_to_tile = {
                    exe.submit(self.download_tile, tile): tile for tile in self.tile_collection.to_list
                }
                for fut in as_completed(future_to_tile):
                    try:
                        results.append(fut.result())
                    except Exception:
                        results.append(False)
                        
                    if pbar:
                        pbar.update(1)
        else:
            for tile in self.tile_collection.to_list:
                res = self.download_tile(tile)
                results.append(res)
                if pbar:
                    pbar.update(1)

        if pbar:
            pbar.close()

        self._evaluate_result(results)
        return self.image_col

    def _evaluate_result(self, result: List):
        success = sum(1 for v in result if v)
        total = len(self.tile_collection)
        logger.info(f"Download completed: {success}/{total} successful ({100*success/total:.1f}%)")
        if success < total:
            logger.warning(f"Failed to download {total - success} tiles")



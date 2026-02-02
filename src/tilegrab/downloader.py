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

        os.makedirs(self.temp_tile_dir, exist_ok=True)
        self.session = self.session or self._init_session()
        self.image_col = TileImageCollection(self.temp_tile_dir)

    def _init_session(self) -> requests.Session:
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

        x,y,z = tile.x,tile.y,tile.z
        url = self.tile_source.get_url(z, x, y)
        headers = self.tile_source.headers() or {}
        tile.url = url

        # print(f"START {url}:{ext}: z:{z} x:{x} y:{y}")
        try:
            resp = self.session.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT) # type: ignore
            resp.raise_for_status()

            if not (resp.headers.get("content-type", "").startswith("image")):
                raise ValueError(
                    f"Unexpected content type {z}/{x}/{y}: "
                    + resp.headers.get("content-type", "")
                )
            
            content = resp.content
            if not content:
                print("Content Error:", content)
                return False
            
            img = TileImage(tile, content)
            self.image_col.append(img)
            return True
        
        except Exception:
            raise RuntimeWarning(f"Failed to fetch {z}/{x}/{y}")

    def run(
        self,
        workers: int = 8,   
        show_progress: bool = True,
    ) -> TileImageCollection:

        results = []
        print(f"    - tile count: {len(self.tiles)}")

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

    def _evaluate_result(self, result:List):
        success = sum(1 for v in result if v)
        print(f"Download completed: {success}/{len(self.tiles)} successful.")

    

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Tuple, Iterable, Optional, Dict
import requests
from requests.adapters import HTTPAdapter, Retry
from tqdm import tqdm
from typing import Tuple

from tilegrab import TileSource
from tilegrab import Tiles


@dataclass
class Downloader:
    tiles: Tiles
    tile_source: TileSource
    output_dir: str = "saved_tiles"
    session: Optional[requests.Session] = None
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 5
    BACKOFF_FACTOR: int = 0
    OVERWRITE: bool = True

    def __post_init__(self):
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = self.session or self._init_session()

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

    def download_tile(self, z: int, x: int, y: int) -> Tuple[str, bool]:

        url = self.tile_source.get_url(z, x, y)
        headers = self.tile_source.headers() or {}

        ext = ".png"
        if ".jpg" in url or ".jpeg" in url:
            ext = ".jpg"
        elif ".png" in url or url.endswith(".png"):
            ext = ".png"
            
        # print(f"START {url}:{ext}: z:{z} x:{x} y:{y}")
        out_path = os.path.join(self.output_dir, f"{z}_{x}_{y}{ext}")

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
                return out_path, False

            self._save(content, out_path)
            return out_path, True
        except Exception:
            raise RuntimeWarning(f"Failed to fetch {z}/{x}/{y}")

    def run(
        self,
        workers: int = 8,
        show_progress: bool = True,
    ) -> Dict[str, bool]:

        results = {}
        print(f"    - tile count: {len(self.tiles)}")

        if show_progress:
            pbar = tqdm(total=len(self.tiles), desc=f"Downloading", unit="tile")
        else:
            pbar = None

        with ThreadPoolExecutor(max_workers=workers) as exe:
            future_to_tile = {
                exe.submit(self.download_tile, tile.z, tile.x, tile.y): tile for tile in self.tiles.to_list
            }
            for fut in as_completed(future_to_tile):
                z, x, y = future_to_tile[fut]
                
                try:
                    path, ok = fut.result()
                    
                except Exception:
                    path, ok = (f"{z}/{x}/{y}", False)

                results[path] = ok
                if pbar:
                    pbar.update(1)
        if pbar:
            pbar.close()
            
        return results

    def _save(self, img, path):

        if os.path.exists(path) and os.path.getsize(path) == 0:
            try:
                os.remove(path)
            except Exception:
                raise RuntimeError("Unable to remove: " + path)

        if (os.path.exists(path) and self.OVERWRITE) or (not os.path.exists(path)):
            with open(path, "wb") as f:
                f.write(img)
        
        # print(f"Done {path}")

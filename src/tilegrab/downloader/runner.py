from dataclasses import dataclass
import logging
import tempfile
from pathlib import Path

from tilegrab.downloader import ProgressStore, ProgressItem
from tilegrab.images import TileImage
from tilegrab.images.loader import load_images
from tilegrab.tiles import TileCollection
from tilegrab.images import TileImageCollection

from .config import DownloadConfig
from .session import create_session
from .worker import DownloadResult, DownloadStatus, download_tile

logger = logging.getLogger(__name__)

#TODO: need to move DownloadStatus.SKIP logic to somewhere else
# `for tile in self.tiles if tile.need_download` also can be used


class Downloader:
    
    def __init__(
        self,
        tile_collection: TileCollection,
        config: DownloadConfig,
        tile_dir: Path | None = None,
    ):
        self.tile_col = tile_collection
        self.config = config
        self.tile_dir = tile_dir or Path(tempfile.mkdtemp())
        self.tile_dir.mkdir(parents=True, exist_ok=True)
        self.progress_store = ProgressStore(self.tile_dir)

    def process_results(self, download_result:DownloadResult):
        
        progress_item = ProgressItem(
            tileIndex=download_result.tile.index,
            downloadStatus=download_result.status,
            tileURL=download_result.url, 
            tileImagePath=self.tile_dir, 
            tileSourceId=self.tile_col.source_uid)
        
        self.progress_store.upsert_by_tile_index(progress_item)
        
        if download_result.status == DownloadStatus.SUCCESS:
            self.images.append(download_result.result)
        
        elif download_result.status == DownloadStatus.SKIP:
            tile_image = load_images(self.tile_dir, [download_result.tile,])
            if len(tile_image) == 1:
                self.images.append(tile_image[0])
        
        elif download_result.status == DownloadStatus.EMPTY:
            logger.warning("downloader.runner returned EMPTY DownloadStatus")
        
        elif download_result.status == DownloadStatus.UNDEFINED:
            logger.error("downloader.runner returned UNDEFINED DownloadStatus")

    def run(
        self,
        workers: int | None = None,
        parallel_download: bool = True,
        show_progress: bool = True,
    ) -> TileImageCollection:
        self.images = []

        def session_factory(): return create_session(self.config)

        if show_progress:
            from tqdm import tqdm
            pbar = tqdm(total=len(self.tile_col), desc="Downloading", unit="tile")
        else:
            pbar = None

        session = session_factory()
        if parallel_download:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        download_tile,
                        tile,
                        session,
                        self.config.timeout,
                    )
                    for tile in self.tile_col
                ]

                for future in as_completed(futures):
                    dl_result = future.result()
                    self.process_results(download_result=dl_result)

                    if pbar:
                        pbar.update(1)
        else:
            for tile in self.tile_col:
                
                dl_result = download_tile(
                    tile=tile, session=session, timeout=self.config.timeout)
                
                self.process_results(download_result=dl_result)
                
                if pbar:
                    pbar.update(1)


        if pbar:
            pbar.close()

        logger.info(
            "Download completed: %d/%d successful",
            len(self.images),
            len(self.tile_col),
        )

        return TileImageCollection.from_images(
            images=self.images, path=self.tile_dir, save=False)


import logging
import tempfile
from pathlib import Path
from typing import List

from tilegrab.images.image import TileImage
from tilegrab.images.loader import load_images
from tilegrab.tiles import TileCollection
from tilegrab.images import TileImageCollection

from .result import DownloadResult
from .progress import ProgressItem, ProgressStore
from .status import DownloadStatus
import tilegrab.downloader.worker as worker
from .config import DownloadConfig
from .session import create_session

logger = logging.getLogger(__name__)


class Downloader:

    def __init__(
        self,
        tile_collection: TileCollection,
        config: DownloadConfig,
        tile_dir: Path | None = None,
        resume: bool = True
    ):
        self.tile_col = tile_collection
        self.config = config
        self.tile_dir = tile_dir or Path(tempfile.mkdtemp())
        self.tile_dir.mkdir(parents=True, exist_ok=True)
        self.progress_store = ProgressStore(self.tile_dir)
        self.resume = resume
        self.images:List[TileImage] = []

        assert len(tile_collection) > 0
        assert any([1 if i.need_download else 0 for i in tile_collection]), [1 if i.need_download else 0 for i in tile_collection]

    def process_results(self, download_result: DownloadResult):

        if download_result.status == DownloadStatus.SUCCESS and download_result.result:
            download_result.result.path = self.tile_dir
            self.images.append(download_result.result)
            
        elif download_result.status == DownloadStatus.SKIP:
            tile_image = load_images(self.tile_dir, [download_result.tile,])
            if len(tile_image) == 1:
                self.images.append(tile_image[0])
                download_result = DownloadResult(
                    download_result.tile,
                    DownloadStatus.SKIP_AND_EXISTS,
                    download_result.result,
                    download_result.url
                )

        elif download_result.status == DownloadStatus.EMPTY:
            logger.warning("downloader.runner returned EMPTY DownloadStatus")

        elif download_result.status == DownloadStatus.UNDEFINED:
            logger.error("downloader.runner returned UNDEFINED DownloadStatus")
        
        # progress update
        progress_item = ProgressItem(
            tileIndex=download_result.tile.index,
            downloadStatus=download_result.status,
            tileURL=download_result.url,
            tileImagePath=self.tile_dir,
            tileSourceId=self.tile_col.source_id,
            saved=self.config.save_images)

        self.progress_store.upsert_by_tile_index(progress_item)

    def run(
        self,
        workers: int | None = None,
        parallel_download: bool = True,
        show_progress: bool = True,
    ) -> TileImageCollection:
        

        def session_factory():
            s = create_session(self.config)
            required_headers = ['referer', 'accept', 'user-agent', 'accept-encoding', 'accept-language']
            assert all([1 if i in s.headers.keys() else 0 for i in  required_headers])
            return s
        
        for idx, tile in enumerate(self.tile_col):
            logger.debug(f"Preparing Tile {idx} {tile.index}")
            progress_item = self.progress_store.progress_by_tile(tile)
            if progress_item:
                if progress_item.downloadStatus == DownloadStatus.SUCCESS and self.resume:
                    # skip this tile
                    self.tile_col[idx].need_download = False
                    logger.debug(f"Excluded from download")
                
                if progress_item.downloadStatus == DownloadStatus.SKIP_AND_EXISTS and self.resume:
                    # skip this tile
                    self.tile_col[idx].need_download = False
                    logger.debug(f"Excluded from download")
        
        logger.debug(f"Total TileImages to be download: {sum([1 for i in self.tile_col if i.need_download])}")

        if show_progress:
            from tqdm import tqdm
            pbar = tqdm(total=len(self.tile_col),
                        desc="       Downloading", unit="tile")
        else:
            pbar = None

        session = session_factory()
        if parallel_download:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        worker.download_tile,
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

                dl_result = worker.download_tile(
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

        img_col = TileImageCollection.from_images(
            images=self.images, 
            path=self.tile_dir
            )
        if self.config.save_images:
            img_col.save()
        
        return img_col

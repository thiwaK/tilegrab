import logging
import tempfile
from pathlib import Path

from tilegrab.tiles import TileCollection
from tilegrab.images import TileImageCollection

from .config import DownloadConfig
from .session import create_session
from .worker import download_tile

logger = logging.getLogger(__name__)


class Downloader:
    
    def __init__(
        self,
        tile_collection: TileCollection,
        config: DownloadConfig,
        temp_dir: Path | None = None,
    ):
        self.tiles = tile_collection
        self.config = config
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        workers: int | None = None,
        parallel_download: bool = True,
        show_progress: bool = True,
    ) -> TileImageCollection:
        images = []

        def session_factory(): return create_session(self.config)

        if show_progress:
            from tqdm import tqdm
            pbar = tqdm(total=len(self.tiles), desc="Downloading", unit="tile")
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
                    for tile in self.tiles
                ]

                for future in as_completed(futures):
                    img = future.result()
                    if img:
                        images.append(img)

                    if pbar:
                        pbar.update(1)
        else:
            for tile in self.tiles:
                img = download_tile(
                    tile=tile, session=session, timeout=self.config.timeout)
                if img:
                    images.append(img)
                
                if pbar:
                    pbar.update(1)


        if pbar:
            pbar.close()

        logger.info(
            "Download completed: %d/%d successful",
            len(images),
            len(self.tiles),
        )

        return TileImageCollection.from_images(images)

#!/usr/bin/env python3
import logging
import argparse
import random
import sys
from pathlib import Path
from tilegrab.downloader import Downloader
from tilegrab.images import TileImageCollection
from tilegrab.tiles import TilesByShape, TilesByBBox
from tilegrab.dataset import GeoDataset
from tilegrab import version

# Configure root logger
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#         logging.FileHandler('tilegrab.log')
#     ]
# )

# Normal colors
BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
GRAY    = "\033[90m"
WHITE  = "\033[37m"

# Bright colors
BBLACK   = "\033[90m"
BRED     = "\033[91m"
BGREEN   = "\033[92m"
BYELLOW  = "\033[93m"
BBLUE    = "\033[94m"
BMAGENTA = "\033[95m"
BCYAN    = "\033[96m"
BGRAY    = "\033[97m"
BWHITE = "\033[97m"

RESET = "\033[0m"


class LogFormatter(logging.Formatter):
    NAME_WIDTH = 14

    LEVEL_MAP = {
        logging.CRITICAL: f'{RED}‼ {RESET}',
        logging.ERROR:    f'{RED}✖ {RESET}',
        logging.WARNING:  f'{YELLOW}⚠ {RESET}',
        logging.INFO:     f'{BLUE}• {RESET}',
        logging.DEBUG:    f'{GRAY}· {RESET}',
        logging.NOTSET:   f'{CYAN}- {RESET}',
    }

    def format(self, record):
        record.level_letter = self.LEVEL_MAP.get(record.levelno, '?')

        short = record.name.rsplit('.', 1)[-1]
        record.short_name = f"{short:<{self.NAME_WIDTH}}"

        return super().format(record)


console_formatter = LogFormatter(
    f'   %(level_letter)s %(message)s'
)
file_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s - %(message)s'
)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(console_formatter )

file = logging.FileHandler('tilegrab.log')
file.setFormatter(file_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console, file],
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="tilegrab", description="Download and mosaic map tiles"
    )

    # Create a named group for the vector polygon source
    extent_source_group = p.add_argument_group(
        title="Source options(Extent)",
        description="Options for the vector polygon source",
    )
    extent_source_group.add_argument(
        "--source",
        type=str,
        required=True,
        help="The vector polygon source for filter tiles",
    )
    extent_group = extent_source_group.add_mutually_exclusive_group(required=True)
    extent_group.add_argument(
        "--shape", action="store_true", help="Use actual shape to derive tiles"
    )
    extent_group.add_argument(
        "--bbox", action="store_true", help="Use shape's bbox to derive tiles"
    )

    # Create a named group for the map tile source
    tile_source_group = p.add_argument_group(
        title="Source options(Map tiles)", description="Options for the map tile source"
    )
    tile_group = tile_source_group.add_mutually_exclusive_group(required=True)
    tile_group.add_argument("--osm", action="store_true", help="OpenStreetMap")
    tile_group.add_argument(
        "--google_sat", action="store_true", help="Google Satellite"
    )
    tile_group.add_argument(
        "--esri_sat", action="store_true", help="ESRI World Imagery"
    )
    tile_group.add_argument(
        "--key", type=str, default=None, help="API key where required by source"
    )

    # other options
    p.add_argument("--zoom", type=int, required=True, help="Zoom level (integer)")
    p.add_argument(
        "--out",
        type=Path,
        default=Path.cwd() / "saved_tiles",
        help="Output directory (default: ./saved_tiles)",
    )
    p.add_argument(
        "--download-only",
        action="store_true",
        help="Only download tiles; do not run mosaicking or postprocessing",
    )
    p.add_argument(
        "--mosaic-only",
        action="store_true",
        help="Only mosaic tiles; do not download",
    )
    p.add_argument(
        "--no-progress", action="store_false", help="Hide download progress bar"
    )
    p.add_argument(
        "--quiet", action="store_true", help="Hide all prints"
    )
    p.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    p.add_argument(
        "--test", action="store_true", help="Only for testing purposes, not for normal use"
    )

    return p.parse_args()


def main():
    args = parse_args()
    
    # Adjust logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        # logger.debug("Debug logging enabled")
    elif args.quiet:
        console.close()
        
    
    
    BANNER_NORMAL, BANNER_BRIGHT = random.choice([
        (RED, BRED),
        (GREEN, BGREEN),
        (YELLOW, BYELLOW),
        (BLUE, BBLUE),
        (MAGENTA, BMAGENTA),
        (CYAN, BCYAN),
        (GRAY, BGRAY),
    ])

    if not args.quiet:
        print()
        print(f"{WHITE}   " + ("-" * 60) + f"{RESET}")
        print(f"{BWHITE}  TileGrab v{version}{RESET}".rjust(50))
        print(f"{WHITE}   " + ("-" * 60) + f"{RESET}")
    
    try:
        dataset = GeoDataset(args.source)
        logger.info(f"Dataset loaded successfully from {args.source}")

        _tmp = "bbox" if args.bbox else "shape" if args.shape else "DnE"
        logger.info(f"""Downloading tiles using {_tmp}
        - minX: {dataset.bbox.minx:.4f}     - minY: {dataset.bbox.miny:.4f}
        - maxX: {dataset.bbox.maxx:.4f}     - maxY: {dataset.bbox.maxy:.4f}
        - zoom: {args.zoom}""")

        if args.shape:
            tiles = TilesByShape(dataset, zoom=args.zoom)
        elif args.bbox:
            tiles = TilesByBBox(dataset, zoom=args.zoom)
        else:
            logger.error("No extent selector selected")
            raise SystemExit("No extent selector selected")

        # Choose source provider
        if args.osm:
            from tilegrab.sources import OSM
            logger.info("Using OpenStreetMap (OSM) as tile source")
            source = OSM(api_key=args.key) if args.key else OSM()
        elif args.google_sat:
            from tilegrab.sources import GoogleSat
            logger.info("Using Google Satellite as tile source")
            source = GoogleSat(api_key=args.key) if args.key else GoogleSat()
        elif args.esri_sat:
            from tilegrab.sources import ESRIWorldImagery
            logger.info("Using ESRI World Imagery as tile source")
            source = ESRIWorldImagery(api_key=args.key) if args.key else ESRIWorldImagery()
        else:
            logger.error("No tile source selected")
            raise SystemExit("No tile source selected")
        
        downloader = Downloader(tiles, source, args.out)
        result: TileImageCollection

        if args.mosaic_only:
            result = TileImageCollection(args.out)
            result.load(tiles)  
        else:
            result = downloader.run(show_progress=args.no_progress)
            logger.info(f"Download result: {result}")
        
        if not args.download_only: result.mosaic()
        logger.info("Done")

        
    except Exception as e:
        logger.exception("Fatal error during execution")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

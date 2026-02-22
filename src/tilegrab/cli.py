#!/usr/bin/env python3
import logging
import argparse
from pathlib import Path
from typing import List
from tilegrab.downloader import Downloader, DownloadConfig
from tilegrab.images import TileImageCollection, ExportType

from tilegrab.logs import setup_logging
from tilegrab.tiles import TilesByShape, TilesByBBox, TileCollection
from tilegrab.dataset import GeoDataset
from tilegrab import __version__


logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="tilegrab", 
        description="Download and mosaic map tiles"
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
    extent_source_group.add_argument("--invert", action="store_true", help="Download the non-overlapping tiles with the source geometry, but with in the bounding box. Works only with --shape")
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

    # Create a named group for merged output format
    mosaic_out_group = p.add_argument_group(
        title="Mosaic export formats", description="Formats for the output mosaic image"
    )
    mosaic_group = mosaic_out_group.add_mutually_exclusive_group(required=False)
    mosaic_group.add_argument("--jpg", action="store_true", help="JPG image; no geo-reference")
    mosaic_group.add_argument("--png", action="store_true", help="PNG image; no geo-reference")
    mosaic_group.add_argument("--tiff", action="store_true", help="GeoTiff image; with geo-reference")
    # mosaic_group.set_defaults(tiff=True)

    # other options
    p.add_argument("--zoom", type=int, required=True, help="Zoom level (integer between 1 and 22)")
    p.add_argument(
        "--tiles-out",
        type=Path,
        default=Path.cwd() / "saved_tiles",
        help="Output directory for downloaded tiles (default: ./saved_tiles)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path.cwd() / "output",
        help="Output directory for the final output (default: ./output)",
    )
    p.add_argument(
        "--download-only",
        action="store_true",
        help="Only download tiles; do not run mosaicking or postprocessing",
    )
    # p.add_argument(
    #     "--resume-download",
    #     action="store_true",
    #     help="Resume the previous download; do not overwrite",
    # )
    p.add_argument(
        "--mosaic-only",
        action="store_true",
        help="Only mosaic tiles; do not download",
    )
    p.add_argument(
        "--group-tiles", type=str, default=None, help="Mosaic tiles but according to given WxH into ./grouped_tiles"
    )
    p.add_argument(
        "--group-overlap", action="store_true", help="Overlap with the next consecutive tile when grouping"
    )
    p.add_argument(
        "--tile-limit", type=int, default=250, help="Override maximum tile limit that can download (use with caution)"
    )
    p.add_argument(
        "--workers", type=int, default=None, help="Max number of threads to use when parallel downloading"
    )
    p.add_argument(
        "--no-parallel",
        action=argparse.BooleanOptionalAction,
        default=True, 
        help="Download tiles sequentially, no parallel downloading"
    )
    p.add_argument(
        "--no-progress", 
        action=argparse.BooleanOptionalAction,
        default=True, 
        help="Hide tile download progress bar"
    )
    p.add_argument("--quiet", action="store_true", help="Hide all prints")
    p.add_argument("--debug", action="store_true", help="Enable debug logging")
    return p.parse_args()

def main():
    LOG_LEVEL = logging.INFO
    ENABLE_CLI_LOG = True
    ENABLE_FILE_LOG = True

    args = parse_args()
    if args.debug:
        LOG_LEVEL = logging.DEBUG
    if args.quiet:
        ENABLE_CLI_LOG = False
    
    setup_logging(ENABLE_CLI_LOG, ENABLE_FILE_LOG, LOG_LEVEL)

    if not args.quiet:
        print()
        print(f"\033[37m   " + ("-" * 60) + "\033[0m")
        print(f"\033[97m  TileGrab v{__version__}\033[0m".rjust(50))
        print(f"\033[37m   " + ("-" * 60) + "\033[0m")

    try:
        dataset = GeoDataset(args.source)
        logger.info(f"Dataset loaded successfully from {args.source}")

        _tmp = "bbox" if args.bbox else "shape" if args.shape else "DnE"
        logger.info(
            f"""Downloading tiles using {_tmp}
        - minX: {dataset.bbox.minx:.4f}     - minY: {dataset.bbox.miny:.4f}
        - maxX: {dataset.bbox.maxx:.4f}     - maxY: {dataset.bbox.maxy:.4f}
        - zoom: {args.zoom}"""
        )

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
            source = (
                ESRIWorldImagery(api_key=args.key) if args.key else ESRIWorldImagery()
            )
        else:
            logger.error("No tile source selected")
            raise SystemExit("No tile source selected")

        tile_collection: TileCollection
        if args.shape:
            tile_collection = TilesByShape(
                geo_dataset=dataset, 
                tile_source=source, 
                zoom=args.zoom, 
                safe_limit=args.tile_limit,
                invert_selection=args.invert
                )
        elif args.bbox:
            tile_collection = TilesByBBox(
                geo_dataset=dataset, tile_source=source, zoom=args.zoom, safe_limit=args.tile_limit
                )
        else:
            logger.error("No extent selector selected")
            raise SystemExit("No extent selector selected")
        
        
        from tilegrab.images import load_images
        tile_image_collection: TileImageCollection
        if args.mosaic_only:
            tile_images = load_images(path=args.tiles_out, tiles=tile_collection)
            tile_image_collection = TileImageCollection(
                path=args.tiles_out, images=tile_images)
            # logger.info(f"Load from disk result: {len(tile_image_collection)} TileImages")
        
        else:
            dl_config = DownloadConfig()
            downloader = Downloader(
                tile_collection=tile_collection,
                config=dl_config,
                tile_dir=args.tiles_out,
                resume=True) #TODO: Always resumes
    
            tile_image_collection = downloader.run(
                workers=args.workers, 
                show_progress=args.no_progress, 
                parallel_download=args.no_parallel)
            
            logger.info(f"Download result: {tile_image_collection}")

            

        img_col_bounds = tile_image_collection.bounds
        ex_types: List[ExportType] = []
        if not args.download_only:
            if args.tiff: 
                ex_types.append(ExportType.TIFF)
            if args.png: 
                ex_types.append(ExportType.PNG)
            if args.jpg: 
                ex_types.append(ExportType.JPG)

            from tilegrab.images import mosaic
            final_img = [mosaic(tile_image_collection), ]

            if args.group_tiles:
                from tilegrab.images import group_image
                w,h = args.group_tiles.lower().split("x")
                final_img = group_image(
                    image=final_img[0], tile_h=256, tile_w=256, group_w=int(w), group_h=int(h))
                
            from tilegrab.images import export_image
            export_image(images=final_img, output_dir=args.out, bounds=img_col_bounds, formats=ex_types)
            
            

        logger.info("Done")

    except Exception as e:
        logger.exception("Fatal error during execution")
        logger.exception(e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()

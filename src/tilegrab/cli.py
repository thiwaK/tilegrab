#!/usr/bin/env python3
import argparse
from pathlib import Path
from tilegrab.downloader import Downloader
from tilegrab.tiles import TilesByShape, TilesByBBox
from tilegrab.dataset import GeoDataset


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
        "--no-progress", action="store_false", help="Hide download progress bar"
    )
    p.add_argument(
        "--quiet", action="store_true", help="Hide all prints"
    )
    

    return p.parse_args()


def main():
    args = parse_args()
    dataset = GeoDataset(args.source)

    _tmp = "bbox" if args.bbox else "shape" if args.shape else "DnE"
    print(f"Downloading tiles... using {_tmp}")
    print()
    print(f"    - minX: {dataset.bbox.minx:.4f}     - minY: {dataset.bbox.miny:.4f}")
    print(f"    - maxX: {dataset.bbox.maxx:.4f}     - maxY: {dataset.bbox.maxy:.4f}")
    print(f"    - zoom: {args.zoom}")

    if args.shape:
        tiles = TilesByShape(dataset, zoom=args.zoom)
    elif args.bbox:
        tiles = TilesByBBox(dataset, zoom=args.zoom)
    else:
        raise SystemExit("No extent selector selected")

    # Choose source provider
    if args.osm:
        from tilegrab.sources import OSM
        source = OSM(api_key=args.key) if args.key else OSM()
    elif args.google_sat:
        from tilegrab.sources import GoogleSat
        source = GoogleSat(api_key=args.key) if args.key else GoogleSat()
    elif args.esri_sat:
        from tilegrab.sources import ESRIWorldImagery
        source = ESRIWorldImagery(api_key=args.key) if args.key else ESRIWorldImagery()
    else:
        raise SystemExit("No tile source selected")

    downloader = Downloader(tiles, source, args.out)
    result = downloader.run(show_progress=args.no_progress)
    success = sum(1 for v in result.values() if v)
    print(f"Download completed: {success}/{len(tiles)} successful.")

    if args.download_only:
        exit()

    print(f"Creating mosaic")
    from tilegrab.mosaic import Mosaic
    mosaic = Mosaic(args.out)
    mosaic.merge(tiles)
    
    print(f"Done.")


if __name__ == "__main__":
    main()

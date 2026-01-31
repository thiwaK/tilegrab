#!/usr/bin/env python3
import argparse
from pathlib import Path
from tilegrab.downloader import Downloader
from tilegrab.tiles import TilesByShape, TilesByBBox
from tilegrab.dataset import GeoDataset

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="tilegrab", description="Download and mosaic map tiles")

    # extent selection: either --shape (use actual geometry) OR --bbox (use geometry's bbox)
    extent_group = p.add_mutually_exclusive_group(required=True)
    extent_group.add_argument(
        "--shape",
        nargs=0,
        type=bool,
        help="Use actual shape to derive tiles"
    )
    extent_group.add_argument(
        "--bbox",
        nargs=0,
        type=bool,
        help="Use shape's bbox to derive tiles"
    )

    # tile source selection (mutually exclusive)
    source_group = p.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--osm", action="store_true", help="OpenStreetMap")
    source_group.add_argument("--google_sat", action="store_true", help="Google Satellite")
    source_group.add_argument("--esri_sat", action="store_true", help="ESRI World Imagery")

    p.add_argument(
        "--source",
        type=str,
        default=None,
        required=True,
        help="The vector polygon source (file path or datasource identifier) for filter tiles"
    )
    p.add_argument("--zoom", type=int, required=True, help="Zoom level (integer)")
    p.add_argument("--out", type=Path, default=Path.cwd() / "saved_tiles",
                   help="Output directory (default: ./saved_tiles)")
    p.add_argument("--download-only", action="store_true",
                   help="Only download tiles; do not run mosaicking or postprocessing")
    p.add_argument("--key", type=str, default=None, help="API key where required by source")

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
    result = downloader.run()
    success = sum(1 for v in result.values() if v)
    print(f"Download completed: {success}/{len(tiles)} successful.")

    if not args.download_only:
        from tilegrab.mosaic import Mosaic
        Mosaic(args.out)

if __name__ == "__main__":
    main()

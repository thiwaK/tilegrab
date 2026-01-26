import argparse
from tilegrab.downloader import Downloader
from tilegrab.sources import OSM
from tilegrab.tiles import TilesByShape

def main():
    parser = argparse.ArgumentParser(
        prog="tilegrab",
        description="Download and mosaic map tiles"
    )

    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    parser.add_argument("--zoom", type=int, required=True)
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    downloader = Downloader(
        TilesByShape()
        OSM(),
    )
    downloader.run()

if __name__ == "__main__":
    main()

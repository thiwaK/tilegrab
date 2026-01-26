#!/usr/bin/env python3

from tilegrab.downloader import Downloader
from tilegrab.dataset import GeoDataset
from tilegrab.mosaic import Mosaic
from tilegrab.sources import OSM, GoogleSat
from tilegrab.tiles import TilesByBBox, TilesByShape



if __name__ == "__main__":

    zoom = 17
    dataset = GeoDataset("SHAPEFILE")
    tiles = TilesByShape(dataset, zoom)
    dl = Downloader(OSM())

    print(f"Downloading tiles...")
    print()
    print(f"    - minX: {dataset.bbox.minx:.4f}     - minY: {dataset.bbox.miny:.4f}")
    print(f"    - maxX: {dataset.bbox.maxx:.4f}     - maxY: {dataset.bbox.maxy:.4f}")
    print(f"    - zoom: {zoom}")

    result = dl.run(workers=8, show_progress=False)
    success = sum(1 for v in result.values() if v)
    print(f"Download completed: {success}/{len(tiles)} successful.")

    print(f"Start merging...")
    Mosaic().merge(tiles)
    print("Done")
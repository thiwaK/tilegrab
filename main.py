#!/usr/bin/env python3

from Core import Downloader, GeoDataset, Moasic, Tiles
from Core.TileSource import OSM, GoogleSat


if __name__ == "__main__":

    zoom = 14
    feature = GeoDataset(r"SHAPEFILE")
    tiles = Tiles(feature, zoom)
    dl = Downloader(OSM())

    print(f"Downloading tiles...")
    print()
    print(f"    - minX: {feature.bbox.minx:.4f}     - minY: {feature.bbox.miny:.4f}")
    print(f"    - maxX: {feature.bbox.maxx:.4f}     - maxY: {feature.bbox.maxy:.4f}")
    print(f"    - zoom: {zoom}")

    result = dl.start(tiles, workers=8, show_progress=False)
    success = sum(1 for v in result.values() if v)
    print(f"Download completed: {success}/{len(tiles)} successful.")

    print(f"Start merging...")
    Moasic().merge(tiles)
    print("Done")
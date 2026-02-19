from functools import cache
import logging
from pathlib import Path
from typing import List, Union
from PIL import Image as PILImage
from tilegrab.images.formats import ExportType
from tilegrab.images.image import TileImage
from tilegrab.tiles import TileCollection
import os
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

logger = logging.getLogger(__name__)


WEB_MERCATOR_EXTENT = 20037508.342789244
EPSG = 3857


class TileImageCollection:
    images: List[TileImage] = []
    width: int = 0
    height: int = 0

    def __init__(self, path: Union[Path, str]) -> None:
        self.path = Path(path)
        logger.info(f"TileImageCollection initialized at {self.path}")

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for i in self.images:
            yield i

    def __repr__(self) -> str:
        return f"ImageCollection; len={len(self)}"

    def _update_collection_dim(self):
        if not self.images:
            logger.warning("Attempting to update collection dimensions with no images")
            return

        x = [img.index.x for img in self.images]
        y = [img.index.y for img in self.images]
        minx, maxx = min(x), max(x)
        miny, maxy = min(y), max(y)
        self.minx, self.maxx = minx, maxx
        self.miny, self.maxy = miny, maxy
        logger.debug(f"Tile range x=({self.minx}, {self.maxx}); y=({self.miny}, {self.maxy})")

        self.width = int((maxx - minx + 1) * self.images[0].width)
        self.height = int((maxy - miny + 1) * self.images[0].height)
       
        
        logger.info(f"Collection dimensions calculated: {self.width}x{self.height}")

    def mosaic_bounds(self, x_min, y_min, x_max, y_max, z):
        n = 2**z
        tile_size_m = 2 * WEB_MERCATOR_EXTENT / n

        xmin = (WEB_MERCATOR_EXTENT * -1) + x_min * tile_size_m
        xmax = (WEB_MERCATOR_EXTENT * -1) + (x_max + 1) * tile_size_m

        ymax = WEB_MERCATOR_EXTENT - y_min * tile_size_m
        ymin = WEB_MERCATOR_EXTENT - (y_max + 1) * tile_size_m

        return xmin, ymin, xmax, ymax

    def load(self, tile_collection: TileCollection):
        import re

        logger.info("Start loading saved ImageTiles")
        pat = re.compile(r"^([0-9]+)_([0-9]+)_([0-9]+)\.[A-Za-z0-9]+$")
        image_col = [p for p in self.path.glob(f"*.*") if p.is_file()]
        self.zoom = tile_collection.to_list[0].index.z
        logger.info(f"Found {len(image_col)} images at {self.path}")

        for tile in tile_collection.to_list:
            found_matching_image = False
            for image_path in image_col:
                m = pat.match(str(image_path.name))
                if m:
                    z = int(m.group(1))
                    x = int(m.group(2))
                    y = int(m.group(3))

                    if tile.index.x == x and tile.index.y == y and tile.index.z == z:
                        logger.debug(f"Processing ImageTile x={x} y={y} z={z}")
                        with open(image_path, "rb") as f:
                            tile_image = TileImage(tile, f.read())
                            tile_image.path = image_path
                            self.images.append(tile_image)
                            found_matching_image = True
                            continue

            if not found_matching_image:
                logger.warning(f"Missing ImageTile x={tile.index.x} y={tile.index.y} z={tile.index.z}")
        
        logger.info(f"{len(self.images)} images loaded, {len(image_col) - len(self.images)} skipped")

        self._update_collection_dim()

    def append(self, img: TileImage):
        img.path = os.path.join(self.path, img.name)
        self.images.append(img)
        logger.debug(f"Image appended to collection: {img.name}")
        img.save()

        self.zoom = img.tile.index.z

    @cache
    def _create_mosaic(self) -> PILImage.Image:
        logger.info("Start mosaicing TileImageCollection")
        self._update_collection_dim()

        logger.info(
            f"Mosaicking {len(self.images)} images into {self.width}x{self.height}"
        )
        merged_image = PILImage.new("RGB", (self.width, self.height))

        for image in self.images:
            px = int((image.index.x) * image.width)
            py = int((image.index.y) * image.height)
            logger.debug(f"Pasting image at position ({px}, {py}): {image.name}")
            merged_image.paste(image.image, (px, py))
        
        return merged_image

    def mosaic(self, export_types: List[int]):
        
        merged_image = self._create_mosaic()
        # TODO: fix this monkey patch
        if ExportType.TIFF in export_types:
            output_path = "mosaic.tiff"
            import numpy as np
            from rasterio.transform import from_bounds
            import rasterio

            data = np.array(merged_image)
            data = data.transpose(2, 0, 1)

            width_px, height_px = merged_image.size
            xmin, ymin, xmax, ymax = self.mosaic_bounds(
                self.minx, self.miny, self.maxx, self.maxy, self.images[0].tile.index.z
            )

            transform = from_bounds(xmin, ymin, xmax, ymax, width_px, height_px)

            with rasterio.open(
                output_path,
                "w",
                driver="GTiff",
                height=height_px,
                width=width_px,
                count=data.shape[0],
                dtype=data.dtype,
                crs=f"EPSG:{EPSG}",
                transform=transform,
            ) as dst:
                dst.write(data)

            logger.info(f"Mosaic saved to {output_path}")
        if ExportType.PNG in export_types:
            output_path = "mosaic.png"
            merged_image.save(output_path)
            logger.info(f"Mosaic saved to {output_path}")
        if ExportType.JPG in export_types:
            output_path = "mosaic.jpg"
            merged_image.save(output_path)
            logger.info(f"Mosaic saved to {output_path}")

    def group(self, width: int, height: int, export_types:List[int], overlap: bool):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive integers")
        
        out_dir = "grouped_tiles"
        os.makedirs(out_dir, exist_ok=True)
        logger.info(f"Start grouping {len(self.images)} TileImages into {width}x{height} groups")

        merged_image= self._create_mosaic()
        merged_image_arr = np.asanyarray(merged_image)

        image_px_width = 256
        image_px_height = 256
        kh, kw = image_px_height*height, image_px_width*width
        view = sliding_window_view(merged_image_arr, (kh, kw, merged_image_arr.shape[2]))
        
        view = view[..., 0, :, :, :]
        OH, OW = view.shape[:2]
        logger.info(f"Saving groups into ./{out_dir}")
        for i in range(0, OH, height*image_px_height):
            for j in range(0, OW, width*image_px_width):
                patch = view[i, j]
                if not (patch == 0).all():
                    img = PILImage.fromarray(patch)
                    if ExportType.PNG in export_types:
                        logger.debug(f"Saving group {i}{j} as {i}{j}.png")
                        img.save(os.path.join(out_dir, f"{i}{j}.png"))
                    if ExportType.JPG in export_types:
                        logger.debug(f"Saving group {i}{j} as {i}{j}.jpg")
                        img.save(os.path.join(out_dir, f"{i}{j}.jpg"))
                    if ExportType.TIFF in export_types:
                        logger.error(f"TIFF exports for tile groups not implemented yet")
                        raise NotImplementedError
                else:
                    logger.debug(f"Skip no-data group {i}{j}")

    def export_collection(self, type: ExportType):
        logger.info(f"Exporting collection as type {type}")
        raise NotImplementedError

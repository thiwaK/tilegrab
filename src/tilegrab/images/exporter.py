import logging
from pathlib import Path
from typing import Iterator, List, Union
from PIL import Image
from tilegrab.images import ImageCollectionBounds
from tilegrab.images import ExportType

logger = logging.getLogger(__name__)
WEB_MERCATOR_EXTENT = 20037508.342789244
EPSG = 3857


def export_image(
    images: Union[List[Image.Image], Iterator[Image.Image]],
    output_dir: Path,
    bounds: ImageCollectionBounds,
    formats: list[ExportType],
):
    output_dir.mkdir(parents=True, exist_ok=True)
    index = ""
    if type(images) == Iterator:
        output_dir = output_dir / "groups"
        logger.info(f"Saving groups into {output_dir}")

        if ExportType.TIFF in formats:
            raise NotImplementedError("Export grouped tiffs currently not supported")

    idx = 1
    for img in images:
        if type(images) == Iterator:
            index = f"{idx}_"

        if ExportType.PNG in formats:
            output_path = f"{index}mosaic.png"
            img.save(output_path)
            logger.info(f"Mosaic saved to {output_path}")

        if ExportType.JPG in formats:
            output_path = f"{index}mosaic.jpg"
            img.save(output_path)
            logger.info(f"Mosaic saved to {output_path}")

        if ExportType.TIFF in formats:
            output_path = f"{index}mosaic.tiff"

            import numpy as np
            from rasterio.transform import from_bounds
            import rasterio

            data = np.array(img)
            data = data.transpose(2, 0, 1)

            width_px, height_px = img.size

            transform = from_bounds(bounds.xmin, bounds.ymin, bounds.xmax, bounds.ymax, width_px, height_px)

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
        
        idx += 1

<div align="center">
    <h1 align="center">TileGrab 🧩</h1>
    <img alt="TileGrab" src="https://img.shields.io/pypi/v/tilegrab.svg">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/tilegrab.svg">
    <img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/tilegrab">
    <img alt="Test Status" src="https://img.shields.io/github/actions/workflow/status/thiwaK/tilegrab/test.yml?branch=main&event=push&style=flat&label=CI">
    <img alt="PyPI - Implementation" src="https://img.shields.io/pypi/implementation/tilegrab">
    <img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/thiwaK/tilegrab">
    <img alt="GitHub License" src="https://img.shields.io/github/license/thiwaK/tilegrab">
    <br/>
    <br/>
</div>


**Fast, scriptable map tile downloader and mosaicker for geospatial workflows.**


`tilegrab` downloads raster map tiles from common providers (OSM, Google Satellite, ESRI World Imagery) using a **vector extent** (polygon shape or bounding box), then optionally mosaics them into a single or multiple rasters.

---

<!-- <p align="center">
  <picture align="center">
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/astral-sh/uv/assets/1309177/03aa9163-1c79-4a87-a31d-7a9311ed9310">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/astral-sh/uv/assets/1309177/629e59c0-9c6e-4013-9ad4-adb2bcf5080d">
    <img alt="Shows a bar chart with benchmark results." src="https://github.com/astral-sh/uv/assets/1309177/629e59c0-9c6e-4013-9ad4-adb2bcf5080d">
  </picture>
</p> -->


## Why tilegrab?

Most tile downloaders have two major drawbacks:
- GUI tools that don’t scale or automate
- Scripts that only support bounding boxes and break on real geometries

`tilegrab` is different:

- Uses **actual vector geometries**, not only just extents 
- Scalable API
- Clean CLI, easy to script and integrate  
- Works with **Shapefiles, GeoPackages, GeoJSON**  
- Supports **download-only**, **mosaic-only** or full pipelines  
- Designed for **GIS, remote sensing, and map production workflows**

---

## Features

- Vector-driven tile selection  
  - Exact geometry-based tile filtering  
  - Or fast bounding-box-based selection  
- Multiple tile providers  
  - OpenStreetMap  
  - Google Satellite  
  - ESRI World Imagery
  - or Custom providers
- Tile mosaicking 
- Progress reporting (optional)  
- API-key support where required  
- Sensible defaults, strict CLI validation  

---

## Installation

### From TestPyPI

#### Stable version
```bash
  pip install -i tilegrab
````

#### Beta version
```bash
  pip install tilegrab==1.2.0b2
````

---

## Quick Start

### Download and mosaic tiles using a polygon

```bash
tilegrab \
  --source boundary.shp \
  --shape \
  --osm \
  --zoom 16
```

### Use bounding box instead of exact geometry

```bash
tilegrab \
  --source boundary.geojson \
  --bbox \
  --esri_sat \
  --zoom 17
```

---

## CLI Usage

```bash
usage: tilegrab [-h] --source SOURCE (--shape | --bbox) (--osm | --google_sat | --esri_sat | --key KEY) (--jpg | --png | --tiff) --zoom ZOOM [--tiles-out TILES_OUT] [--download-only] [--mosaic-only]
                [--group-tiles GROUP_TILES] [--group-overlap] [--tile-limit TILE_LIMIT] [--workers WORKERS] [--no-parallel] [--no-progress] [--quiet] [--debug]

Download and mosaic map tiles

options:
  -h, --help            show this help message and exit
  --zoom ZOOM           Zoom level (integer between 1 and 22)
  --tiles-out TILES_OUT
                        Output directory for downloaded tiles (default: ./saved_tiles)
  --download-only       Only download tiles; do not run mosaicking or postprocessing
  --mosaic-only         Only mosaic tiles; do not download
  --group-tiles GROUP_TILES
                        Mosaic tiles but according to given WxH into ./grouped_tiles
  --group-overlap       Overlap with the next consecutive tile when grouping
  --tile-limit TILE_LIMIT
                        Override maximum tile limit that can download (use with caution)
  --workers WORKERS     Max number of threads to use when parallel downloading
  --no-parallel         Download tiles sequentially, no parallel downloading
  --no-progress         Hide tile download progress bar
  --quiet               Hide all prints
  --debug               Enable debug logging

Source options(Extent):
  Options for the vector polygon source

  --source SOURCE       The vector polygon source for filter tiles
  --shape               Use actual shape to derive tiles
  --bbox                Use shape's bbox to derive tiles

Source options(Map tiles):
  Options for the map tile source

  --osm                 OpenStreetMap
  --google_sat          Google Satellite
  --esri_sat            ESRI World Imagery
  --key KEY             API key where required by source

Mosaic export formats:
  Formats for the output mosaic image

  --jpg                 JPG image; no geo-reference
  --png                 PNG image; no geo-reference
  --tiff                GeoTiff image; with geo-reference

```

---


## Supported Vector Formats

Any format readable by **GeoPandas**, including:

* Shapefile (`.shp`)
* GeoPackage (`.gpkg`)
* GeoJSON (`.geojson`)
* Spatial databases (via supported drivers)

---

## Custom Tile Sources (Bring Your Own Provider)

`tilegrab` is **not limited** to built-in providers.

If a tile service follows the standard `{z}/{x}/{y}` pattern, you can add it in **one small class** by extending `TileSource`.


### Example

```python
from tilegrab.sources import TileSource

class MyCustomSource(TileSource):
    name = "MyCustomSource name"
    description = "MyCustomSource description"
    url_template = "https://MyCustomSource/{z}/{x}/{y}.png"
```


---


### get_url Function

You can change how the url is generate by override `get_url` function, inside your Custom Tile Sources. If you are planning to use API key, you must override this function.

```python
def get_url(self, z: int, x: int, y: int) -> str:
  assert self.api_key
  return self.url_template.format(x=x, y=y, z=z, token=self.api_key)
```

### URL Template Rules

Your tile source **must** define:
* `url_template`
  Must contain `{z}`, `{x}`, `{y}` placeholders.

Optional but recommended:
* `name` – Human-readable name
* `description` – Short description of the imagery


---

### API Keys

If your provider requires an API key, pass it during instantiation:

```python
source = MyCustomSource(api_key="YOUR_KEY")
```

---


### Using a Custom Source in Code

Custom sources are intended for **programmatic use** (not CLI flags):

```python
from tilegrab.downloader import Downloader
from tilegrab.tiles import TilesByShape
from tilegrab.dataset import GeoDataset

dataset = GeoDataset("area.gpkg")
tile_collection = TilesByShape(dataset, zoom=16)
tile_source = MyCustomSource(api_key="XYZ")
downloader = Downloader(tile_collection, tile_source, "output")
downloader.run()
```

This keeps the CLI clean while giving developers full control.

---

### Why This Design?

* Zero configuration overhead
* No registry or plugin boilerplate
* Easy to vendor in private or internal tile servers
* Safe default for public CLI usage

If you need full flexibility, use the Python API.

---

<!-- ## Project Structure

```text
tilegrab/
├── cli.py          # CLI entry point
├── dataset.py      # Vector dataset handling
├── tiles.py        # Tile calculation logic
├── downloader.py   # Tile download engine
├── mosaic.py       # Tile mosaicking
└── sources.py      # Tile providers
``` 

---
-->

<!-- ## Who This Is For

* GIS analysts automating basemap generation
* Remote sensing workflows needing tiled imagery
* Developers building spatial data pipelines
* Anyone tired of manual tile grabbing

If you want a GUI, this isn’t it.
If you want control, repeatability, and speed — it is.

--- -->

## Roadmap

Planned (not promises):

* Additional tile providers
* Parallel download tuning
* Raster reprojection and resampling options
* Expanded Python API documentation
* Test implementation

---

## License

MIT License.
Do whatever you want — just don’t pretend you wrote it.

---

## Author

**Thiwanka Munasinghe**
GitHub: [https://github.com/thiwaK](https://github.com/thiwaK)

```
```
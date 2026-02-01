
<div align="center">
    <h1 align="center">TileGrab 🧩</h1>
    <!-- until publish on PyPi -->
    <img alt="TileGrab" src="https://img.shields.io/badge/testpypi-1.0.0-blue">
    <!-- <img alt="TileGrab" src="https://img.shields.io/pypi/v/tilegrab.svg"> -->
    <img alt="TileGrab - Python Versions" src="https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11|%203.12|%203.13-blue">
    <!-- <img alt="TileGrab - Python Versions" src="https://img.shields.io/pypi/pyversions/tilegrab.svg"> -->
    <!--  -->
    <img alt="Test Status" src="https://img.shields.io/github/actions/workflow/status/thiwaK/tilegrab/test.yml?branch=main&event=push&style=flat&label=test">
    <br/>
    <br/>
</div>


**Fast, scriptable map tile downloader and mosaicker for geospatial workflows.**


`tilegrab` downloads raster map tiles from common providers (OSM, Google Satellite, ESRI World Imagery) using a **vector extent** (polygon or bounding box), then optionally mosaics them into a single raster. Built for automation, reproducibility, and real GIS work — not GUI clicking.

---

<!-- <p align="center">
  <picture align="center">
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/astral-sh/uv/assets/1309177/03aa9163-1c79-4a87-a31d-7a9311ed9310">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/astral-sh/uv/assets/1309177/629e59c0-9c6e-4013-9ad4-adb2bcf5080d">
    <img alt="Shows a bar chart with benchmark results." src="https://github.com/astral-sh/uv/assets/1309177/629e59c0-9c6e-4013-9ad4-adb2bcf5080d">
  </picture>
</p> -->


## Why tilegrab?

Most tile downloaders fall into one of two traps:
- GUI tools that don’t scale or automate
- Scripts that only support bounding boxes and break on real geometries

`tilegrab` is different:

- Uses **actual vector geometries**, not just extents  
- Clean CLI, easy to script and integrate  
- Works with **Shapefiles, GeoPackages, GeoJSON**  
- Supports **download-only**, **mosaic-only**, or full pipelines  
- Designed for **GIS, remote sensing, and map production workflows**

No magic. No black boxes.

---

## Features

- Vector-driven tile selection  
  - Exact geometry-based tile filtering  
  - Or fast bounding-box-based selection  
- Multiple tile providers  
  - OpenStreetMap  
  - Google Satellite  
  - ESRI World Imagery  
- Automatic tile mosaicking  
- Progress reporting (optional)  
- API-key support where required  
- Sensible defaults, strict CLI validation  

---

## Installation

### From TestPyPI

```bash
  pip install -i https://test.pypi.org/simple/tilegrab
````

> [!NOTE]
> A stable PyPI release will follow once the API is finalized.

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
usage: tilegrab [-h] --source SOURCE (--shape | --bbox) (--osm | --google_sat | --esri_sat | --key KEY) --zoom ZOOM [--out OUT] [--download-only] [--mosaic-only] [--no-progress] [--quiet]

Download and mosaic map tiles

options:
  -h, --help       show this help message and exit
  --zoom ZOOM      Zoom level (integer)
  --out OUT        Output directory (default: ./saved_tiles)
  --download-only  Only download tiles; do not run mosaicking or postprocessing
  --mosaic-only    Only mosaic tiles; do not download
  --no-progress    Hide download progress bar
  --quiet          Hide all prints

Source options(Extent):
  Options for the vector polygon source

  --source SOURCE  The vector polygon source for filter tiles
  --shape          Use actual shape to derive tiles
  --bbox           Use shape's bounding box to derive tiles

Source options(Map tiles):
  Options for the map tile source

  --osm            OpenStreetMap
  --google_sat     Google Satellite
  --esri_sat       ESRI World Imagery
  --key KEY        API key where required by source
```

---
<!-- 
## Required Arguments

| Argument   | Description                               |
| ---------- | ----------------------------------------- |
| `--source` | Vector dataset used to derive tile extent |
| `--shape`  | Use exact geometry to select tiles        |
| `--bbox`   | Use geometry bounding box                 |
| `--zoom`   | Web map zoom level                        |

---

## Tile Sources (CLI)

| Flag           | Source             |
| -------------- | ------------------ |
| `--osm`        | OpenStreetMap      |
| `--google_sat` | Google Satellite   |
| `--esri_sat`   | ESRI World Imagery |

Optional API key:

```bash
--key YOUR_API_KEY
```

---

## Output & Processing Options

| Option            | Description                                 |
| ----------------- | ------------------------------------------- |
| `--out <dir>`     | Output directory (default: `./saved_tiles`) |
| `--download-only` | Download tiles only                         |
| `--mosaic-only`   | Mosaic existing tiles only                  |
| `--no-progress`   | Disable progress bar                        |
| `--quiet`         | Suppress console output                     |

--- 
-->

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

No registration. No plugin system. No magic.

---

### Example

```python
from tilegrab.sources import TileSource

class MyCustomSource(TileSource):
    name = "MyCustomSource name"
    description = "MyCustomSource description"
    URL_TEMPLATE = "https://MyCustomSource/{z}/{x}/{y}.png"
```

That’s it.

Once instantiated, the source works exactly like built-in providers.

---


### get_url Function

You can change how the url is generate by override `get_url` function, inside your Custom Tile Sources. If you are planning to use API key, you must override this function.

```python
def get_url(self, z: int, x: int, y: int) -> str:
  assert self.api_key
  return self.URL_TEMPLATE.format(x=x, y=y, z=z, token=self.api_key)
```

### URL Template Rules

Your tile source **must** define:

* `URL_TEMPLATE`
  Must contain `{z}`, `{x}`, `{y}` placeholders.

Optional but recommended:

* `name` – Human-readable name
* `description` – Short description of the imagery

Example templates:

```text
https://server/{z}/{x}/{y}.png
https://tiles.example.com/{z}/{x}/{y}.jpg
https://api.provider.com/tiles/{z}/{x}/{y}?key={token}
```

---

### API Keys

If your provider requires an API key, pass it during instantiation:

```python
source = MyCustomSource(api_key="YOUR_KEY")
```

`TileSource` already handles key injection — you don’t need to reinvent it.

---


### Using a Custom Source in Code

Custom sources are intended for **programmatic use** (not CLI flags):

```python
from tilegrab.downloader import Downloader
from tilegrab.tiles import TilesByShape
from tilegrab.dataset import GeoDataset

dataset = GeoDataset("area.gpkg")
tiles = TilesByShape(dataset, zoom=16)

source = MyCustomSource(api_key="XYZ")
downloader = Downloader(tiles, source, "output")
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

## Project Structure

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

## Who This Is For

* GIS analysts automating basemap generation
* Remote sensing workflows needing tiled imagery
* Developers building spatial data pipelines
* Anyone tired of manual tile grabbing

If you want a GUI, this isn’t it.
If you want control, repeatability, and speed — it is.

---

## Roadmap

Planned (not promises):

* Additional tile providers
* Parallel download tuning
* Cloud-optimized raster output
* Raster reprojection and resampling options
* Expanded Python API documentation

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
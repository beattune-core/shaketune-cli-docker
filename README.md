# shaketune-cli-docker

A Docker image that runs [Klippain Shaketune](https://github.com/Frix-x/klippain-shaketune) locally and exposes a browser-based UI for generating input shaper graphs — no running Klipper printer required.

## What it does

Upload your raw accelerometer data (`.csv`) through the web UI, select a graph type, configure parameters, and get a ShakeTune PNG graph back in the browser.

Powered by:
- [Klippain Shaketune](https://github.com/Frix-x/klippain-shaketune) for graph generation
- [Klipper](https://github.com/Klipper3d/klipper) (cloned at build time, used as a dependency)
- [Gradio](https://gradio.app) for the pure-Python web UI

## Supported graph types

| Graph type | Description |
|---|---|
| `input_shaper` | Calibrate input shaper settings |
| `belts` | Compare belt tension (CoreXY / CoreXZ) |

## Generating raw measurement data

Use Klipper's `TEST_RESONANCES` command to capture raw accelerometer data. The resulting `.csv` files are what you upload to this tool.

> **Do not** use `SHAPER_CALIBRATE` — it produces processed `calibration_data_*.csv` files that cannot be used as input here.

### Input Shaper

Run one command per axis. Upload one or both files together.

```
TEST_RESONANCES AXIS=X
TEST_RESONANCES AXIS=Y
```

Files are saved to `/tmp/` as `resonances_x_YYYYMMDD_HHMMSS.csv` and `resonances_y_YYYYMMDD_HHMMSS.csv`.

### Belts (CoreXY)

Run both diagonal directions. Upload both files together.

```
TEST_RESONANCES AXIS=1,-1
TEST_RESONANCES AXIS=-1,1
```

Files are saved to `/tmp/` as `resonances_1_-1_YYYYMMDD_HHMMSS.csv` and `resonances_-1_1_YYYYMMDD_HHMMSS.csv`.

## Usage with Docker Compose

### Run with remote image

```bash
docker-compose up -d
```

Open [http://localhost:7860](http://localhost:7860) in your browser.

### Stop

```bash
docker-compose down
```

### Optional environment variables

Edit `docker-compose.yml` and modify `SHAKETUNE_TIMEOUT`:

```yaml
environment:
  - SHAKETUNE_TIMEOUT=180
```

### Build and run locally

```bash
docker-compose up -d --build
```

> **Note:** The first build takes several minutes because numpy is compiled from source against OpenBLAS on Alpine Linux.

## Publishing

The image is built and published automatically via GitHub Actions on every push to `main` (tagged `latest`) and on version tags like `v1.0.0`.

Image registry: `ghcr.io/beattune-core/shaketune-cli-docker`

## License

This repository is MIT licensed. Shaketune and Klipper are subject to their own respective licenses.

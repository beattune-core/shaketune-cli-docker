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

Use Klipper's `TEST_RESONANCES` command with `OUTPUT=raw_data` to capture raw accelerometer data. The resulting `.csv` files are what you upload to this tool.

> **Important:** Always add `OUTPUT=raw_data`. Without it, Klipper writes a processed PSD file (`resonances_x_*.csv` with a `freq,psd_x,...` header) that shaketune cannot use as input. `SHAPER_CALIBRATE` also produces unusable output (`calibration_data_*.csv`).

### Input Shaper

Run one command per axis. Upload one or both files together.

```
TEST_RESONANCES AXIS=X OUTPUT=raw_data
TEST_RESONANCES AXIS=Y OUTPUT=raw_data
```

Files are saved to `/tmp/` as `resonances_x_YYYYMMDD_HHMMSS.csv` and `resonances_y_YYYYMMDD_HHMMSS.csv`.

### Belts (CoreXY)

Run both diagonal directions. Upload both files together.

```
TEST_RESONANCES AXIS=1,-1 OUTPUT=raw_data
TEST_RESONANCES AXIS=-1,1 OUTPUT=raw_data
```

Files are saved to `/tmp/` as `resonances_1_-1_YYYYMMDD_HHMMSS.csv` and `resonances_-1_1_YYYYMMDD_HHMMSS.csv`.

## Usage

### Pull and run

```bash
docker run -d \
  --name shaketune \
  -p 7860:7860 \
  ghcr.io/beattune-core/shaketune-cli-docker:latest
```

Open [http://localhost:7860](http://localhost:7860) in your browser.

### Stop

```bash
docker stop shaketune && docker rm shaketune
```

### Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `SHAKETUNE_TIMEOUT` | `120` | Seconds before graph generation is aborted |

```bash
docker run -d \
  --name shaketune \
  -p 7860:7860 \
  -e SHAKETUNE_TIMEOUT=180 \
  ghcr.io/beattune-core/shaketune-cli-docker:latest
```

## Building locally

```bash
git clone https://github.com/beattune-core/shaketune-cli-docker.git
cd shaketune-cli-docker

docker build -t shaketune-cli-docker:local .

docker run -d --name shaketune -p 7860:7860 shaketune-cli-docker:local
```

> **Note:** The first build takes several minutes because numpy is compiled from source against OpenBLAS on Alpine Linux.

## Publishing

The image is built and published automatically via GitHub Actions on every push to `main` (tagged `latest`) and on version tags like `v1.0.0`.

Image registry: `ghcr.io/beattune-core/shaketune-cli-docker`

## License

This repository is MIT licensed. Shaketune and Klipper are subject to their own respective licenses.

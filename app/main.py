import os
import shutil
import subprocess
import uuid
from pathlib import Path

import gradio as gr

PYTHON = "/app/.venv/bin/python"
KLIPPER_DIR = "/app/klipper"
WORK_DIR = Path("/tmp/shaketune")
GRAPH_TYPES = ["belts", "input_shaper"]
ALLOWED_EXTENSIONS = {".csv", ".stdata"}
TIMEOUT = int(os.environ.get("SHAKETUNE_TIMEOUT", "120"))

GRAPH_PARAMS = {
    "belts":        {"kinematics", "mode", "accel_per_hz", "sweeping_accel", "sweeping_period", "max_scale"},
    "input_shaper": {"scv", "max_smoothing", "mode", "accel_per_hz", "sweeping_accel", "sweeping_period", "max_scale"},
}


_PSD_MSG = (
    "{name} is a processed PSD file, not raw accelerometer data. "
    "Run TEST_RESONANCES with OUTPUT=raw_data to get the correct file:\n"
    "  TEST_RESONANCES AXIS=X OUTPUT=raw_data"
)


def _validate_csv_header(path: str) -> None:
    name = Path(path).name
    with open(path) as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            # Klipper shaper_calibrate.py writes PSD header WITHOUT leading #
            if stripped.startswith("freq,psd_x,psd_y,psd_z,psd_xyz"):
                raise gr.Error(_PSD_MSG.format(name=name))
            # Older Klipper / shaketune internal PSD header WITH leading #
            if stripped.startswith("#freq,psd_x,psd_y,psd_z,psd_xyz"):
                raise gr.Error(_PSD_MSG.format(name=name))
            if stripped.startswith("#time,accel_x,accel_y,accel_z"):
                return
            if not stripped.startswith("#"):
                break
    raise gr.Error(
        f"{name} does not have a recognised Klipper raw accelerometer header. "
        "Expected '#time,accel_x,accel_y,accel_z'.\n"
        "Run TEST_RESONANCES with OUTPUT=raw_data:\n"
        "  TEST_RESONANCES AXIS=X OUTPUT=raw_data"
    )


def generate_graph(
    files, graph_type,
    max_freq, dpi,
    scv, max_smoothing,
    kinematics,
    mode, accel_per_hz, sweeping_accel, sweeping_period, max_scale,
):
    if not files:
        raise gr.Error("Upload at least one input file.")
    if not graph_type:
        raise gr.Error("Select a graph type.")
    if graph_type == "belts" and len(files) < 2:
        raise gr.Error("Belts comparison requires two input files (one per belt direction).")

    tmpdir = WORK_DIR / str(uuid.uuid4())
    tmpdir.mkdir(parents=True, exist_ok=True)
    output_path = tmpdir / "output.png"
    input_paths = []

    try:
        for f in files:
            src = Path(f)
            if src.suffix not in ALLOWED_EXTENSIONS:
                raise gr.Error(f"Unsupported file type: {src.suffix}. Use .csv or .stdata.")
            dst = tmpdir / src.name
            shutil.copy(src, dst)
            input_paths.append(str(dst))

        for path in input_paths:
            if Path(path).suffix == ".csv":
                _validate_csv_header(path)

        cmd = [PYTHON, "-m", "shaketune.cli", graph_type, "-o", str(output_path)]
        cmd += input_paths
        cmd += ["--klipper_dir", KLIPPER_DIR]

        def opt(flag, value):
            if value is not None and value != "":
                cmd.extend([flag, str(value)])

        opt("--max_freq", max_freq)
        opt("--dpi", dpi)

        relevant = GRAPH_PARAMS.get(graph_type, set())
        if "scv" in relevant:
            opt("--scv", scv)
        if "max_smoothing" in relevant:
            opt("--max_smoothing", max_smoothing)
        if "kinematics" in relevant:
            opt("--kinematics", kinematics)
        if "mode" in relevant:
            opt("--mode", mode)
        if "accel_per_hz" in relevant:
            opt("--accel_per_hz", accel_per_hz)
        if "sweeping_accel" in relevant:
            opt("--sweeping_accel", sweeping_accel)
        if "sweeping_period" in relevant:
            opt("--sweeping_period", sweeping_period)
        if "max_scale" in relevant:
            opt("--max_scale", max_scale)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env={**os.environ, "SHAKETUNE_IN_CLI": "1"},
        )

        if result.returncode != 0:
            output = "\n".join(s for s in (result.stdout, result.stderr) if s.strip())
            raise gr.Error(f"shaketune error:\n{output}")

        if not output_path.exists():
            raise gr.Error("shaketune ran successfully but produced no output file.")

        return str(output_path)

    except subprocess.TimeoutExpired:
        raise gr.Error(f"Graph generation timed out after {TIMEOUT}s.")
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"Unexpected error: {e}")
    finally:
        for path in input_paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass


# --- UI ---

with gr.Blocks(title="Shaketune Web UI") as demo:
    gr.Markdown("# Klippain Shaketune\nUpload accelerometer data and generate input shaper graphs.")

    with gr.Row():
        with gr.Column(scale=1):
            files_input = gr.File(
                label="Input files (.csv or .stdata)",
                file_count="multiple",
                file_types=[".csv", ".stdata"],
            )
            graph_type = gr.Dropdown(choices=GRAPH_TYPES, label="Graph type")

            with gr.Group():
                max_freq = gr.Number(label="Max frequency (Hz)", value=None, precision=1)
                dpi = gr.Number(label="DPI", value=None, precision=0)

            with gr.Group(visible=False) as grp_input_shaper:
                gr.Markdown("**Input Shaper**")
                scv = gr.Number(label="Square corner velocity in mm/s (default: 5.0)", value=5.0, precision=1)
                max_smoothing = gr.Number(label="Max smoothing (optional)", value=None, precision=3)

            with gr.Group(visible=False) as grp_belts:
                gr.Markdown("**Belts**")
                kinematics_b = gr.Dropdown(
                    choices=["", "corexy", "corexz"],
                    label="Kinematics (optional)",
                    value="",
                )

            with gr.Group(visible=False) as grp_advanced:
                gr.Markdown("**Advanced**")
                mode = gr.Textbox(label="Mode (optional)", placeholder="e.g. SWEEPING", value="")
                accel_per_hz = gr.Number(label="Accel per Hz (optional)", value=None, precision=2)
                sweeping_accel = gr.Number(label="Sweeping accel (optional)", value=None, precision=1)
                sweeping_period = gr.Number(label="Sweeping period (optional)", value=None, precision=2)
                max_scale = gr.Number(label="Max scale (optional)", value=None, precision=0)

            generate_btn = gr.Button("Generate graph", variant="primary")

        with gr.Column(scale=2):
            output_image = gr.Image(label="Result", type="filepath")

    def update_groups(gt):
        return {
            grp_input_shaper: gr.update(visible=gt == "input_shaper"),
            grp_belts:        gr.update(visible=gt == "belts"),
            grp_advanced:     gr.update(visible=gt in {"belts", "input_shaper"}),
        }

    graph_type.change(
        update_groups,
        inputs=graph_type,
        outputs=[grp_input_shaper, grp_belts, grp_advanced],
    )

    generate_btn.click(
        generate_graph,
        inputs=[
            files_input, graph_type, max_freq, dpi,
            scv, max_smoothing,
            kinematics_b,
            mode, accel_per_hz, sweeping_accel, sweeping_period, max_scale,
        ],
        outputs=output_image,
        api_name="generate",
    )


demo.launch(server_name="0.0.0.0", server_port=7860)

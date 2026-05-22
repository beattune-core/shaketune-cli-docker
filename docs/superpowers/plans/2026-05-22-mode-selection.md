# Mode Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the optional free-text mode field with a PULSE/SWEEPING dropdown for input shaper, hardcode PULSE for belts, and show sweeping parameters only when SWEEPING is selected.

**Architecture:** All changes are in `app/main.py`. The `generate_graph` function gains explicit mode handling (hardcoded PULSE for belts, UI-driven for input shaper) and sweeping validation. The UI gains two new groups (`grp_mode`, `grp_sweeping`) and a new `mode.change` event handler. `GRAPH_PARAMS` is trimmed to remove mode and sweeping entries now handled explicitly.

**Tech Stack:** Python 3.12, Gradio (gr.Dropdown, gr.Number, gr.Group), shaketune CLI (`--mode`, `--sweeping_accel`, `--sweeping_period`)

---

### Task 1: Update `GRAPH_PARAMS` and `generate_graph` logic

**Files:**
- Modify: `app/main.py:16-19` (GRAPH_PARAMS)
- Modify: `app/main.py:54-143` (generate_graph)

- [ ] **Step 1: Update GRAPH_PARAMS** — remove `mode`, `sweeping_accel`, `sweeping_period` (now handled explicitly)

```python
GRAPH_PARAMS = {
    "belts":        {"kinematics", "accel_per_hz", "max_scale"},
    "input_shaper": {"scv", "max_smoothing", "accel_per_hz", "max_scale"},
}
```

- [ ] **Step 2: Add sweeping validation** — insert after the existing `len(files) < 2` check at line 66:

```python
    if graph_type == "input_shaper" and mode == "SWEEPING":
        if not sweeping_accel:
            raise gr.Error("Sweeping accel is required when mode is SWEEPING.")
        if not sweeping_period:
            raise gr.Error("Sweeping period is required when mode is SWEEPING.")
```

- [ ] **Step 3: Replace mode/sweeping CLI building** — remove the four `if "mode" in relevant` / `if "sweeping_accel" in relevant` / `if "sweeping_period" in relevant` blocks (lines 104–111) and replace with:

```python
        # Mode: always passed for both graph types
        if graph_type == "input_shaper":
            cmd += ["--mode", mode]
        else:
            cmd += ["--mode", "PULSE"]

        # Sweeping params: only when SWEEPING mode (input_shaper only)
        if graph_type == "input_shaper" and mode == "SWEEPING":
            opt("--sweeping_accel", sweeping_accel)
            opt("--sweeping_period", sweeping_period)
```

The full `generate_graph` cmd-building block after these changes (for reference):

```python
        opt("--max_freq", max_freq)
        opt("--dpi", dpi)

        relevant = GRAPH_PARAMS.get(graph_type, set())
        if "scv" in relevant:
            opt("--scv", scv)
        if "max_smoothing" in relevant:
            opt("--max_smoothing", max_smoothing)
        if "kinematics" in relevant:
            opt("--kinematics", kinematics)
        if "accel_per_hz" in relevant:
            opt("--accel_per_hz", accel_per_hz)
        if "max_scale" in relevant:
            opt("--max_scale", max_scale)

        # Mode: always passed for both graph types
        if graph_type == "input_shaper":
            cmd += ["--mode", mode]
        else:
            cmd += ["--mode", "PULSE"]

        # Sweeping params: only when SWEEPING mode (input_shaper only)
        if graph_type == "input_shaper" and mode == "SWEEPING":
            opt("--sweeping_accel", sweeping_accel)
            opt("--sweeping_period", sweeping_period)
```

- [ ] **Step 4: Verify the file parses** — run from the project root (outside the container, just syntax check):

```bash
python -c "import ast; ast.parse(open('app/main.py').read()); print('OK')"
```

Expected output: `OK`

---

### Task 2: Rebuild the UI groups

**Files:**
- Modify: `app/main.py:164-214` (UI section)

- [ ] **Step 1: Replace `grp_advanced`** — remove the old `grp_advanced` block (lines 177–183) containing `mode` Textbox, `sweeping_accel`, `sweeping_period`, `accel_per_hz`, `max_scale`, and replace with three separate groups:

```python
            # Mode — input_shaper only
            with gr.Group(visible=False) as grp_mode:
                gr.Markdown("**Mode**")
                mode = gr.Dropdown(
                    choices=["PULSE", "SWEEPING"],
                    label="Mode",
                    value="PULSE",
                )

            # Sweeping params — shown only when mode = SWEEPING
            with gr.Group(visible=False) as grp_sweeping:
                gr.Markdown("**Sweeping parameters**")
                sweeping_accel = gr.Number(label="Sweeping accel (mm/s²)", value=None, precision=1)
                sweeping_period = gr.Number(label="Sweeping period (s)", value=None, precision=2)

            # Advanced — both graph types
            with gr.Group(visible=False) as grp_advanced:
                gr.Markdown("**Advanced**")
                accel_per_hz = gr.Number(label="Accel per Hz (optional)", value=None, precision=2)
                max_scale = gr.Number(label="Max scale (optional)", value=None, precision=0)
```

- [ ] **Step 2: Verify the file parses**

```bash
python -c "import ast; ast.parse(open('app/main.py').read()); print('OK')"
```

Expected: `OK`

---

### Task 3: Update event handlers and button wiring

**Files:**
- Modify: `app/main.py:190-213` (event handlers + generate_btn.click)

- [ ] **Step 1: Replace `update_groups`** — update to handle the three new groups:

```python
    def update_groups(gt):
        return {
            grp_input_shaper: gr.update(visible=gt == "input_shaper"),
            grp_belts:        gr.update(visible=gt == "belts"),
            grp_mode:         gr.update(visible=gt == "input_shaper"),
            grp_sweeping:     gr.update(visible=False),  # always reset on graph type change
            grp_advanced:     gr.update(visible=gt in {"belts", "input_shaper"}),
        }

    graph_type.change(
        update_groups,
        inputs=graph_type,
        outputs=[grp_input_shaper, grp_belts, grp_mode, grp_sweeping, grp_advanced],
    )
```

- [ ] **Step 2: Add `mode.change` handler** — insert after the `graph_type.change` wiring:

```python
    def update_sweeping(md):
        return gr.update(visible=md == "SWEEPING")

    mode.change(
        update_sweeping,
        inputs=mode,
        outputs=grp_sweeping,
    )
```

- [ ] **Step 3: Update `generate_btn.click` inputs** — `sweeping_accel` and `sweeping_period` are now defined in `grp_sweeping` instead of `grp_advanced`. The widget variable names are unchanged so the inputs list stays identical:

```python
    generate_btn.click(
        generate_graph,
        inputs=[
            files_input, graph_type, max_freq, dpi,
            scv, max_smoothing,
            kinematics_b,
            mode, accel_per_hz, sweeping_accel, sweeping_period, max_scale,
        ],
        outputs=output_image,
        api_name="/generate",
    )
```

- [ ] **Step 4: Verify the file parses**

```bash
python -c "import ast; ast.parse(open('app/main.py').read()); print('OK')"
```

Expected: `OK`

---

### Task 4: Update integration tests

**Files:**
- Modify: `tests/test_input_shaper.py`
- Modify: `tests/conftest.py`

The `gradio_predict` helper in `conftest.py` passes parameters positionally matching the `inputs=[...]` list. The list order is unchanged, but `mode` is now a dropdown with a default of `"PULSE"` — pass it explicitly. `sweeping_accel` and `sweeping_period` remain `None` for the PULSE test.

- [ ] **Step 1: Update `conftest.py` `gradio_predict`** — `mode` now has a meaningful default (`"PULSE"`). Update the helper to default to `"PULSE"` instead of `""`:

```python
    def _predict(files, gt, **kwargs):
        return gradio_client_instance.predict(
            [handle_file(str(f)) for f in files],
            gt,
            kwargs.get("max_freq", None),
            kwargs.get("dpi", None),
            kwargs.get("scv", None),
            kwargs.get("max_smoothing", None),
            kwargs.get("kinematics_b", ""),
            kwargs.get("mode", "PULSE"),        # updated default
            kwargs.get("accel_per_hz", None),
            kwargs.get("sweeping_accel", None),
            kwargs.get("sweeping_period", None),
            kwargs.get("max_scale", None),
            api_name="/generate",
        )
```

- [ ] **Step 2: Update `test_input_shaper.py`** — pass mode explicitly for clarity:

```python
from conftest import SAMPLES


def test_input_shaper(gradio_predict, assert_png):
    result = gradio_predict(
        files=[SAMPLES / "input_shaper.csv"],
        gt="input_shaper",
        scv=5.0,
        mode="PULSE",
    )
    assert_png(result)
```

---

### Task 5: Build and smoke-test the container

- [ ] **Step 1: Build the image**

```bash
docker build -t shaketune-cli-docker:local .
```

Expected: build completes without error.

- [ ] **Step 2: Swap the running container**

```bash
docker stop shaketune && docker rm shaketune
docker run -d --name shaketune -p 7860:7860 shaketune-cli-docker:local
```

- [ ] **Step 3: Manual smoke test**
  - Open `http://localhost:7860`
  - Select `input_shaper` → confirm **Mode group** appears with `PULSE` selected
  - Change mode to `SWEEPING` → confirm **Sweeping parameters** group appears
  - Change mode back to `PULSE` → confirm sweeping group disappears
  - Select `belts` → confirm Mode group is hidden
  - Generate an input shaper graph with mode=PULSE → confirm graph title shows `| Mode: PULSE`
  - Generate a belts graph → confirm graph title shows `| Mode: PULSE`

- [ ] **Step 4: Commit**

```bash
git add app/main.py tests/test_input_shaper.py tests/conftest.py
git commit -m "feat: add PULSE/SWEEPING mode dropdown for input shaper"
```

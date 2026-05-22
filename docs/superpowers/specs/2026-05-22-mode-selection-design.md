# Mode Selection Design

**Date:** 2026-05-22
**Scope:** `app/main.py` — Gradio UI and `generate_graph` function

## Problem

The generated input shaper graph shows `| Mode: None` because no `--mode` value is passed to the shaketune CLI. Belts graphs have the same problem. The user needs to select between PULSE (standard `TEST_RESONANCES OUTPUT=raw_data`) and SWEEPING (sweeping resonance test), and supply sweeping parameters when SWEEPING is chosen.

## Shaketune mode behaviour (from source)

- `--mode` is a free-form string passed to the CLI; shaketune displays it as-is in the graph title: `| Mode: <value>`
- The only string with special handling is `SWEEPING` (exact case): the plotter appends `[sweeping period: X s - accel: Y mm/s²]` to the title
- Both `shaper_plotter.py` and `belts_plotter.py` contain identical `if mode == 'SWEEPING'` checks

## Design

### Input Shaper

Add a **Mode group** (`grp_mode`) visible only when `graph_type == "input_shaper"`:

| Field | Type | Default | Notes |
|---|---|---|---|
| `mode` | `gr.Dropdown` | `"PULSE"` | Choices: `["PULSE", "SWEEPING"]` |

Add a **Sweeping group** (`grp_sweeping`) visible only when `graph_type == "input_shaper"` AND `mode == "SWEEPING"`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `sweeping_accel` | `gr.Number` | Yes | mm/s², precision 1 |
| `sweeping_period` | `gr.Number` | Yes | seconds, precision 2 |

### Belts

No UI changes. Hardcode `--mode PULSE` in `generate_graph` for belts. Fixes `| Mode: None` on belt graphs.

### Advanced group

Remove `mode`, `sweeping_accel`, and `sweeping_period`. Retain `accel_per_hz` and `max_scale`.

## Event handlers

| Event | Inputs | Action |
|---|---|---|
| `graph_type.change` | `graph_type` | Show `grp_mode` when `input_shaper`; always hide `grp_sweeping` on graph type change (safe reset); show `grp_advanced` for both types |
| `mode.change` | `mode` | Show `grp_sweeping` when `SWEEPING`, hide otherwise |

`grp_sweeping` is always hidden on `graph_type.change` regardless of the current mode value — the user must re-select SWEEPING after switching graph type if needed. This avoids needing to read the current mode state inside the graph_type handler.

## Validation (in `generate_graph`)

```python
if graph_type == "input_shaper" and mode == "SWEEPING":
    if not sweeping_accel:
        raise gr.Error("Sweeping accel is required when mode is SWEEPING.")
    if not sweeping_period:
        raise gr.Error("Sweeping period is required when mode is SWEEPING.")
```

## CLI command changes

- Input shaper: always passes `--mode <value>` (PULSE or SWEEPING)
- Belts: always passes `--mode PULSE` (hardcoded, no UI)
- `sweeping_accel` and `sweeping_period` only appended to cmd when mode is SWEEPING

## Files changed

- `app/main.py` — UI groups, event handlers, `generate_graph` validation and cmd building

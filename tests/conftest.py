import os
import time
from pathlib import Path

import pytest
import requests

SAMPLES = Path(__file__).parent / "samples"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="session")
def base_url():
    url = os.environ.get("SHAKETUNE_URL", "http://localhost:7860")
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=3).ok:
                return url
        except requests.ConnectionError:
            pass
        time.sleep(3)
    pytest.fail(f"Container at {url} did not become ready within 120s")


@pytest.fixture(scope="session")
def gradio_client_instance(base_url):
    from gradio_client import Client
    return Client(base_url, verbose=False)


@pytest.fixture(scope="session")
def assert_png():
    def _assert(result):
        path = Path(result)
        assert path.exists(), f"Output file not found: {path}"
        data = path.read_bytes()
        assert data[:8] == PNG_MAGIC, f"Result is not a valid PNG (got {data[:8]!r})"
    return _assert


@pytest.fixture(scope="session")
def gradio_predict(gradio_client_instance):
    """
    Call the /generate endpoint. Omitted params fall back to safe defaults.

    Parameter order matches inputs=[...] in generate_btn.click():
      files, graph_type, max_freq, dpi,
      scv, max_smoothing,
      kinematics_b (belts),
      mode, accel_per_hz, sweeping_accel, sweeping_period, max_scale
    """
    from gradio_client import handle_file

    def _predict(files, gt, **kwargs):
        return gradio_client_instance.predict(
            [handle_file(str(f)) for f in files],
            gt,
            kwargs.get("max_freq", None),
            kwargs.get("dpi", None),
            kwargs.get("scv", None),
            kwargs.get("max_smoothing", None),
            kwargs.get("kinematics_b", ""),
            kwargs.get("mode", "PULSE"),
            kwargs.get("accel_per_hz", None),
            kwargs.get("sweeping_accel", None),
            kwargs.get("sweeping_period", None),
            kwargs.get("max_scale", None),
            api_name="/generate",
        )

    return _predict

from conftest import SAMPLES


def test_input_shaper(gradio_predict, assert_png):
    result = gradio_predict(
        files=[SAMPLES / "input_shaper.csv"],
        gt="input_shaper",
        scv=5.0,
        mode="PULSE",
    )
    assert_png(result)

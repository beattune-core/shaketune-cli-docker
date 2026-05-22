from conftest import SAMPLES

INPUT_SHAPER = SAMPLES / "input_shaper"


def test_input_shaper(gradio_predict, assert_png):
    result = gradio_predict(
        files=[
            INPUT_SHAPER / "raw_data_x_lis2dw_20260423_171429.csv",
            INPUT_SHAPER / "raw_data_y_lis2dw_20260507_220315.csv",
        ],
        gt="input_shaper",
        scv=5.0,
        mode="PULSE",
    )
    assert_png(result)

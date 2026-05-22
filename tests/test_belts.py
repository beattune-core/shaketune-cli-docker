from conftest import SAMPLES

BELTS = SAMPLES / "belts"


def test_belts(gradio_predict, assert_png):
    result = gradio_predict(
        files=[BELTS / "belt_a.csv", BELTS / "belt_b.csv"],
        gt="belts",
        kinematics_b="corexy",
    )
    assert_png(result)

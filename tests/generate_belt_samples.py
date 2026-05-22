"""
Generate synthetic Klipper raw accelerometer CSV files for belt comparison tests.
Run once from the project root: python tests/generate_belt_samples.py
"""
import numpy as np
from pathlib import Path

SAMPLE_RATE = 3200  # Hz — ADXL345 default
DURATION = 10       # seconds
OUTPUT_DIR = Path(__file__).parent / "samples" / "belts"


def generate_belt_csv(path: Path, resonance_hz: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    n = int(DURATION * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE

    # Chirp sweep 5→150 Hz on the X axis to simulate a belt resonance test
    f0, f1 = 5.0, 150.0
    k = (f1 - f0) / DURATION
    chirp = np.sin(2 * np.pi * (f0 * t + 0.5 * k * t**2))

    # Amplify around the resonance frequency to create a visible peak
    freq_at_t = f0 + k * t
    envelope = 1.0 + 8.0 * np.exp(-((freq_at_t - resonance_hz) ** 2) / (2 * 4.0**2))

    accel_x = envelope * chirp * 3000 + rng.normal(0, 80, n)
    accel_y = rng.normal(0, 80, n)
    accel_z = 9800.0 + rng.normal(0, 80, n)  # gravity on Z

    with open(path, "w") as f:
        f.write("#time,accel_x,accel_y,accel_z\n")
        for i in range(n):
            f.write(f"{t[i]:.6f},{accel_x[i]:.6f},{accel_y[i]:.6f},{accel_z[i]:.6f}\n")

    print(f"Written {path.name}  ({n} samples, peak at {resonance_hz} Hz)")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_belt_csv(OUTPUT_DIR / "belt_a.csv", resonance_hz=42.0, seed=1)
    generate_belt_csv(OUTPUT_DIR / "belt_b.csv", resonance_hz=47.0, seed=2)
    print("Done.")

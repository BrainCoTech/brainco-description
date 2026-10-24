"""Batch-compatible entry point for the backtrim_v4 URDF-to-USD settings.

Usage: python convert_urdf_v4.py input.urdf output.usd --headless --flatten

Defaults match the v4 export: fixed base, merged fixed joints, zero drive gains,
disabled gravity, self-collision and solver iterations 16/4. Revo3 palm and thumb
settings are detected for each hand. Use --collision-only to retain the legacy
drive, gravity, solver and fixed-joint defaults.
"""

from convert_urdf_new import run


if __name__ == "__main__":
    run(v4=True)

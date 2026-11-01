"""Verify and read this parameter bundle; Python standard library only."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTOR_FIELDS = (
    "armature_kg_m2",
    "viscous_Nm_s_rad",
    "friction_Nm",
    "encoder_bias_rad",
    "effective_kp_Nm_rad",
    "effective_kd_Nm_s_rad",
    "effective_effort_limit_Nm",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_bundle(root=ROOT):
    root = Path(root).resolve()
    hashes = read_json(root / "checksums.json")
    for name, expected in hashes.items():
        path = (root / name).resolve()
        if (
            not path.is_relative_to(root)
            or not path.is_file()
            or digest(path) != expected
        ):
            raise ValueError(f"Bundle integrity check failed: {name}")
    return len(hashes)


def load_model(model="fit_03", root=ROOT):
    """Return (parameters, hand) after integrity, shape and SI value checks."""
    if model not in ("fit_03", "balanced"):
        raise ValueError("Choose fit_03 or balanced")
    root = Path(root)
    verify_bundle(root)
    directory = root / "models" / model
    p = read_json(directory / "best_parameters.json")
    h = read_json(directory / "hand.json")
    frozen = read_json(directory / "selection_frozen.json")
    if digest(directory / "best_parameters.json") != frozen["parameters_sha256"]:
        raise ValueError("Frozen parameter hash mismatch")
    names = h["joint_names"]
    expected_names = [
        r["joint"] for r in read_json(root / "bundle_info.json")["joint_mapping"]
    ]
    if len(names) != 21 or names != expected_names or len(set(names)) != 21:
        raise ValueError("Joint order mismatch")
    for field in VECTOR_FIELDS:
        values = p[field]
        if len(values) != 21 or not all(math.isfinite(v) for v in values):
            raise ValueError(f"Invalid vector: {field}")
        if field != "encoder_bias_rad" and min(values) < 0:
            raise ValueError(f"Negative value: {field}")
    if not math.isfinite(p["delay_s"]) or not 0 <= p["delay_s"] <= 1:
        raise ValueError("Invalid delay")
    if (
        not math.isfinite(p["finger_body_inertia_scale"])
        or p["finger_body_inertia_scale"] <= 0
    ):
        raise ValueError("Invalid inertia scale")
    return p, h


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["fit_03", "balanced"], default="fit_03")
    args = parser.parse_args()
    p, h = load_model(args.model)
    print(
        json.dumps(
            {
                "verified_files": verify_bundle(),
                "model": args.model,
                "joint_count": len(h["joint_names"]),
                "parameter_fields": list(p),
                "delay_s_saved": p["delay_s"],
                "pd_period_s": h["dt_s"],
                "delay_steps": math.floor(p["delay_s"] / h["dt_s"] + 0.5),
                "hardware_commands_issued": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

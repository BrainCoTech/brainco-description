"""Replay one recorded stage in Newton; no hardware connection or optimization."""

import argparse
from pathlib import Path

from load_parameters import load_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["fit_03", "balanced"], default="fit_03")
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--prepare-only", action="store_true", help="Check input without starting GPU"
    )
    args = parser.parse_args()
    import numpy as np
    from revo3_sysid.gui_mit_data import load_raw, episode
    from revo3_sysid.io import atomic_output, write_json

    parameters, hand = load_model(args.model)
    raw = load_raw(args.raw)
    ep = episode(raw, args.stage, hand["dt_s"])
    if ep["joint_names"].tolist() != hand["joint_names"]:
        raise ValueError("Recorded joint order does not match model")
    if args.out.exists():
        raise FileExistsError(args.out)
    if args.prepare_only:
        print(
            f"Prepared {args.stage}: {len(ep['time_s'])} samples, 21 joints; GPU not started"
        )
        return
    from revo3_sysid.backends.newton import NewtonRollout

    # Full hand, two physical substeps per 5 ms PD tick; preserve self-collision.
    hand = dict(hand, physics_substeps=2)
    args.out.mkdir(parents=True, exist_ok=False)
    sim = NewtonRollout(hand, batch=1, device=args.device)
    try:
        prediction, diagnostics = sim.run(
            ep, [parameters], delay_mode="command", require_no_contact=True
        )
        with atomic_output(args.out / "prediction.npz", overwrite=False) as stream:
            np.savez_compressed(
                stream,
                time_s=ep["time_s"],
                joint_names=ep["joint_names"],
                predicted_rad=prediction[0],
                measured_rad=ep["q_measured_rad"],
            )
        write_json(
            args.out / "report.json",
            {
                "completed": True,
                "model": args.model,
                "stage": args.stage,
                "source_sha256": raw["source_sha256"],
                "hardware_commands_issued": 0,
                "diagnostics": diagnostics,
            },
        )
    finally:
        sim.close()


if __name__ == "__main__":
    main()

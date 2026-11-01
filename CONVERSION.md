# Generate MJCF and USD locally

> **Since release 20261025, customers must generate MJCF and USD on their own
> machines.** Git contains URDF models, meshes/textures and these conversion
> tools. Generated `*_system/mjcf/` and `*_system/usd/` directories are ignored.
> **从 20261025 起，客户需要自行运行转换脚本生成 MJCF 和 USD；克隆仓库不会包含这两类产物。**

## Commands

**dev / 2026-11-01:** the non-tactile `revo3_right.urdf` now contains 144
pre-decomposed convex parts (90 shared meshes). Its USD import automatically
uses per-part convex hulls; MJCF reuses meshes by path and scale. Other variants
retain their previous collision profiles. See
[Revo3 URDF migration](revo3_system/URDF_COLLISIONS.md) for commands, counts,
Isaac Lab 3.0 validation, and the original zero-effort joint-limit caveat.

Run from the downloaded repository after preparing the appropriate environment:

```bash
./convert_all_urdf_to_mjcf.sh
./convert_all_urdf_to_usd.sh
```

No conversion arguments are required. Each script locates the model directories
relative to itself, so invoking it by an absolute path from another directory
also works. Neither conversion requires ROS, Xacro, robot drivers or the
maintainer's source workspace. The public 20261025 release contains 29 URDFs;
the scripts convert all packaged URDFs present in the supported system folders.

| Entry point | Default | Output per URDF |
| --- | --- | --- |
| `convert_all_urdf_to_mjcf.sh` | `--method urdf` | `<system>/mjcf/<name>.xml` |
| `convert_all_urdf_to_usd.sh` | `--flatten`, fixed base, headless | `<system>/usd/<name>.usd` |

Re-running replaces outputs with the same names. To preserve a previous model
version or custom simulation edits, use a separate checkout or copy first.
Running the converters does not commit or upload their outputs.

## MJCF environment

Use Bash and Python 3.10 or later. The converter itself uses only Python's
standard library; MuJoCo is needed to load or simulate its output, not to write
the XML. Tested with Python 3.10 and MuJoCo 3.3.7 for loading/forward computation.

```bash
./convert_all_urdf_to_mjcf.sh

# Optional: install MuJoCo in your chosen environment to load the generated XML.
python3 -m pip install mujoco==3.3.7
```

The default copies link masses and inertia tensors from URDF. Visual and
collision geoms use groups 2 and 3 respectively; visual geoms do not collide.
Colors, screen textures and tactile marker primitives are retained. Screen DAE
meshes are converted to OBJ under `mjcf/meshes/` automatically. Actuators,
tendons, control policies and task-specific contact exclusions are not added.

## USD environment

Install a compatible Isaac Sim / Isaac Lab environment and activate it before
running the USD entry point. An ordinary system Python or `usd-core` alone is
insufficient for this converter. Follow the
[Isaac Lab 2.3.2 installation guide](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/index.html)
for installation and its GPU/driver requirements.

Validated conversion environment:

| Component | Version |
| --- | --- |
| OS | Ubuntu 22.04 |
| Python | 3.11.15 |
| Isaac Sim | 5.1.0 (package metadata: `5.1.0.0`) |
| Isaac Lab | 2.3.2 (`VERSION`; extension package metadata: `0.54.3`) |

After activating that environment, confirm that its `python3` is selected:

```bash
python3 -c 'from isaaclab.app import AppLauncher; print("Isaac Lab available")'
./convert_all_urdf_to_usd.sh
```

The converter starts Isaac Sim once for the batch, uses fixed bases, merges fixed
joints, sets drive stiffness/damping to zero, disables body gravity, enables
self-collision and uses solver iterations 16/4. It retains the Revo3 trimmed
palm and 32 thumb collision hulls for hands using the old profile; migrated
right-hand parts instead retain their 144 explicit hulls. Exported files are reopened to check
collision/physics settings, colors and screen textures. These are the validated
conversion defaults; application controllers remain the user's responsibility.

Flattening removes generated configuration USD layers and sidecars. Images
remain external: preserve the system's `meshes/` directory and its relative
paths when moving a USD model. Generated `usd/` alone is not a complete bundle.

Different Isaac Sim / Isaac Lab releases may change importer APIs and generated
content. Use the tested versions for this release; compatibility with arbitrary
newer versions is not implied.

## Optional overrides and diagnostics

Normal use needs no arguments. These options are available for maintainers:

```bash
# Inspect the batch without needing Isaac Sim or writing output.
./convert_all_urdf_to_usd.sh --dry-run

# Select a prepared Isaac Lab interpreter explicitly.
./convert_all_urdf_to_usd.sh --python /path/to/environment/bin/python

# Convert a different packaged model root.
OUT_DIR=/path/to/models ./convert_all_urdf_to_mjcf.sh
OUT_DIR=/path/to/models ./convert_all_urdf_to_usd.sh
```

`MJCF_PYTHON` and `ISAACSIM_PYTHON` optionally select interpreters; both default
to the active environment's `python3`. No personal Conda path is assumed.
`--help` lists advanced options, including alternate MJCF inertia methods and
USD `--no-flatten`. Missing models, unavailable dependencies or failed
conversions produce a nonzero exit status. If Isaac Sim startup fails, check
the selected environment and GPU/driver setup before retrying.

## Tool files

The two shell entry points and these Python helpers must be kept together:

- `urdf_to_mjcf.py`: URDF-to-MJCF geometry, inertia, materials and textures.
- `convert_urdf_v4.py`: USD entry point with the validated v4 settings.
- `convert_urdf_new.py`: Isaac Lab batch import, flattening and validation.
- `revo3_collision_v4.py`: Revo3 USD collision settings and checks.

Use a tagged checkout to keep URDF assets and converter code at the same
version. Older tags still contain prebuilt files and historical Git LFS objects;
this release does not require downloading those objects.

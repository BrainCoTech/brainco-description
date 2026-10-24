# BrainCo Robot Description Assets

> **IMPORTANT — Local conversion required since 20261025.**
> **MJCF and USD files are no longer included in Git. Customers must generate them locally.**
> The repository ships URDF, meshes/textures and complete conversion tools.
> **从 20261025 起，客户需要自行运行转换脚本生成 MJCF 和 USD；克隆仓库不再包含预生成文件。**

After preparing the appropriate Python environment, run these commands from the repository root:

```bash
./convert_all_urdf_to_mjcf.sh   # default: --method urdf
./convert_all_urdf_to_usd.sh    # default: --flatten; requires Isaac Lab / Isaac Sim
```

No conversion arguments are needed. See [environment setup and conversion guide](CONVERSION.md)
before running the USD command. Generated outputs are ignored by Git.

This repository contains public robot description assets for BrainCo robot hands, arms, and combined arm-hand systems. The package is intended for simulation, visualization, integration testing, and downstream robotics research.

The public release includes 29 URDF descriptions, their mesh/texture assets, and tools to generate MJCF and USD locally.

Current release: **20261025**. See [Release Notes](RELEASE_NOTES.md) for version history and model validation status.

## What Is Included

| System | Description | Included in Git | Generated locally |
| --- | --- | --- | --- |
| `revo2_system` | Revo2 left and right dexterous hands | URDF + assets | MJCF, USD |
| `revo3_system` | Revo3 left and right dexterous hands | URDF + assets | MJCF, USD |
| `revoarm_system` | Single-arm and bimanual RevoArm assemblies with Revo2/Revo3 hands | URDF + assets | MJCF, USD |
| `revotron_system` | Single-arm and bimanual RevoTron platform assemblies with Revo3 hands | URDF + assets | MJCF, USD |

## Visual Catalog

The rendered previews below correspond to the robot description entry points in this repository. `Arm: None` means the model is a standalone dexterous hand with no arm assembly.

Revo3 models are available in three variants: unsuffixed files have no tactile
markers, `_mx_touch` files include MX markers, and `_mt_touch` files include MT
markers. All three variants are provided as URDF for standalone hands and the
RevoArm/RevoTron assemblies; the converters generate matching MJCF and USD.
MJCF/USD paths in the catalog below are output locations and exist only after conversion.

The existing previews were rendered from URDF visual geometry in the zero joint
configuration and are retained from the previous release. They have not been
refreshed for the updated MX markers, and MT previews are not included yet.

### Standalone Hands

| Preview | Description files | Arm | Hand | Configuration | Side |
| --- | --- | --- | --- | --- | --- |
| <img src="visualizations/revo2_system/urdf/revo2_left.png" alt="revo2_left" width="120"> | URDF: `revo2_system/urdf/revo2_left.urdf`<br>MJCF: `revo2_system/mjcf/revo2_left.xml`<br>USD: `revo2_system/usd/revo2_left.usd` | None | Revo2 | Single hand | Left |
| <img src="visualizations/revo2_system/urdf/revo2_right.png" alt="revo2_right" width="120"> | URDF: `revo2_system/urdf/revo2_right.urdf`<br>MJCF: `revo2_system/mjcf/revo2_right.xml`<br>USD: `revo2_system/usd/revo2_right.usd` | None | Revo2 | Single hand | Right |
| <img src="visualizations/revo3_system/urdf/revo3_left.png" alt="revo3_left" width="120"> | URDF: `revo3_system/urdf/revo3_left.urdf`<br>MJCF: `revo3_system/mjcf/revo3_left.xml`<br>USD: `revo3_system/usd/revo3_left.usd` | None | Revo3 | Single hand | Left |
| <img src="visualizations/revo3_system/urdf/revo3_right.png" alt="revo3_right" width="120"> | URDF: `revo3_system/urdf/revo3_right.urdf`<br>MJCF: `revo3_system/mjcf/revo3_right.xml`<br>USD: `revo3_system/usd/revo3_right.usd` | None | Revo3 | Single hand | Right |

### RevoArm Assemblies

| Preview | Description files | Arm | Hand | Configuration | Side |
| --- | --- | --- | --- | --- | --- |
| <img src="visualizations/revoarm_system/urdf/revoarm_single_left_revo2.png" alt="revoarm_single_left_revo2" width="120"> | URDF: `revoarm_system/urdf/revoarm_single_left_revo2.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_single_left_revo2.xml`<br>USD: `revoarm_system/usd/revoarm_single_left_revo2.usd` | RevoArm | Revo2 | Single arm | Left |
| <img src="visualizations/revoarm_system/urdf/revoarm_single_right_revo2.png" alt="revoarm_single_right_revo2" width="120"> | URDF: `revoarm_system/urdf/revoarm_single_right_revo2.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_single_right_revo2.xml`<br>USD: `revoarm_system/usd/revoarm_single_right_revo2.usd` | RevoArm | Revo2 | Single arm | Right |
| <img src="visualizations/revoarm_system/urdf/revoarm_bimanual_revo2.png" alt="revoarm_bimanual_revo2" width="120"> | URDF: `revoarm_system/urdf/revoarm_bimanual_revo2.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_bimanual_revo2.xml`<br>USD: `revoarm_system/usd/revoarm_bimanual_revo2.usd` | RevoArm | Revo2 | Bimanual | Left + right |
| <img src="visualizations/revoarm_system/urdf/revoarm_single_left_revo3.png" alt="revoarm_single_left_revo3" width="120"> | URDF: `revoarm_system/urdf/revoarm_single_left_revo3.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_single_left_revo3.xml`<br>USD: `revoarm_system/usd/revoarm_single_left_revo3.usd` | RevoArm | Revo3 | Single arm | Left |
| <img src="visualizations/revoarm_system/urdf/revoarm_single_right_revo3.png" alt="revoarm_single_right_revo3" width="120"> | URDF: `revoarm_system/urdf/revoarm_single_right_revo3.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_single_right_revo3.xml`<br>USD: `revoarm_system/usd/revoarm_single_right_revo3.usd` | RevoArm | Revo3 | Single arm | Right |
| <img src="visualizations/revoarm_system/urdf/revoarm_bimanual_revo3.png" alt="revoarm_bimanual_revo3" width="120"> | URDF: `revoarm_system/urdf/revoarm_bimanual_revo3.urdf`<br>MJCF: `revoarm_system/mjcf/revoarm_bimanual_revo3.xml`<br>USD: `revoarm_system/usd/revoarm_bimanual_revo3.usd` | RevoArm | Revo3 | Bimanual | Left + right |

### RevoTron Assemblies

| Preview | Description files | Arm | Hand | Configuration | Side |
| --- | --- | --- | --- | --- | --- |
| <img src="visualizations/revotron_system/urdf/revotron_single_left_revo3.png" alt="revotron_single_left_revo3" width="120"> | URDF: `revotron_system/urdf/revotron_single_left_revo3.urdf`<br>MJCF: `revotron_system/mjcf/revotron_single_left_revo3.xml`<br>USD: `revotron_system/usd/revotron_single_left_revo3.usd` | RevoTron | Revo3 | Single arm | Left |
| <img src="visualizations/revotron_system/urdf/revotron_single_right_revo3.png" alt="revotron_single_right_revo3" width="120"> | URDF: `revotron_system/urdf/revotron_single_right_revo3.urdf`<br>MJCF: `revotron_system/mjcf/revotron_single_right_revo3.xml`<br>USD: `revotron_system/usd/revotron_single_right_revo3.usd` | RevoTron | Revo3 | Single arm | Right |
| <img src="visualizations/revotron_system/urdf/revotron_bimanual_revo3.png" alt="revotron_bimanual_revo3" width="120"> | URDF: `revotron_system/urdf/revotron_bimanual_revo3.urdf`<br>MJCF: `revotron_system/mjcf/revotron_bimanual_revo3.xml`<br>USD: `revotron_system/usd/revotron_bimanual_revo3.usd` | RevoTron | Revo3 | Bimanual | Left + right |

## Using the Models

Clone the repository (or download this tag's source archive), then generate
the simulation format you need. Git LFS is not required for the current release;
older tags still contain historical LFS-tracked USD files.

```bash
git clone --branch 20261025 https://github.com/BrainCoTech/brainco-description.git
cd brainco-description

# Python 3.10+; generation uses only the Python standard library.
./convert_all_urdf_to_mjcf.sh

# Activate your configured Isaac Lab / Isaac Sim environment first.
./convert_all_urdf_to_usd.sh
```

The tested USD environment is Isaac Sim 5.1.0 with Isaac Lab 2.3.2 and Python
3.11 on Ubuntu 22.04. Setup instructions and optional interpreter overrides are
in [CONVERSION.md](CONVERSION.md). Neither converter requires ROS or robot drivers.

URDF and the generated MJCF/USD models retain the complete visual appearance.

URDF files can be loaded by common robotics tools such as ROS, RViz, Pinocchio, and other URDF-compatible parsers.

After MJCF generation, the files can be loaded with MuJoCo:

```python
import mujoco

model = mujoco.MjModel.from_xml_path(
    "revoarm_system/mjcf/revoarm_bimanual_revo3.xml"
)
data = mujoco.MjData(model)
```

After USD generation, the files can be opened with USD-compatible tools such as `usdview` or loaded in NVIDIA Isaac Sim / Isaac Lab:

```bash
usdview revo3_system/usd/revo3_left.usd
```

The generated USD files, such as `revo3_system/usd/revo3_left.usd`, are flattened
entry points. They do not require generated configuration USD layers, but their
screen textures still reference images under `meshes/`. Preserve those relative paths.

Mesh paths are stored as relative paths, so load models from the repository root or preserve the directory layout when copying files into another project.

## Notes For Simulation

- MJCF files separate visual and collision geometry where applicable. Visual geoms are intended for rendering, while collision geoms are intended for contact simulation.
- USD files include the converted robot hierarchy, visual and collision geometry, PhysX articulation metadata, and Isaac robot/link/joint metadata where applicable.
- The models are provided as description assets. Controller gains, task-space policies, calibration data, and application-specific simulation settings are intentionally left to downstream projects.

## Work In Progress

The public asset set is still evolving. Planned or ongoing work includes:

- MJCF actuator definitions and control-ready simulation settings.
- Additional validation across common robotics and simulation toolchains.

## License

License information will be provided with the public release. Please review the accompanying license before redistributing or modifying these assets.

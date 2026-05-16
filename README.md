# BrainCo Robot Description Assets

This repository contains public robot description assets for BrainCo robot hands, arms, and combined arm-hand systems. The package is intended for simulation, visualization, integration testing, and downstream robotics research.

The public release includes URDF, MJCF, and USD descriptions, together with the mesh assets they reference.

## What Is Included

| System | Description | Formats |
| --- | --- | --- |
| `revo2_system` | Revo2 left and right dexterous hands | URDF, MJCF, USD |
| `revo3_system` | Revo3 left and right dexterous hands | URDF, MJCF, USD |
| `revoarm_system` | Single-arm and bimanual RevoArm assemblies with Revo2/Revo3 hands | URDF, MJCF, USD |
| `revotron_system` | Revotron bimanual platform assemblies | URDF, MJCF, USD |

## Repository Layout

```text
.
├── revo2_system/
│   ├── meshes/
│   ├── urdf/
│   ├── mjcf/
│   └── usd/
├── revo3_system/
│   ├── meshes/
│   ├── urdf/
│   ├── mjcf/
│   └── usd/
├── revoarm_system/
│   ├── meshes/
│   ├── urdf/
│   ├── mjcf/
│   └── usd/
└── revotron_system/
    ├── meshes/
    ├── urdf/
    ├── mjcf/
    └── usd/
```

Each system directory follows the same convention:

- `urdf/`: URDF robot description files.
- `mjcf/`: MuJoCo XML model files.
- `usd/`: OpenUSD robot description files for visualization and Isaac Sim / Isaac Lab workflows.
- `meshes/`: Visual and collision geometry referenced by the descriptions.
- `README.md`: Optional system-specific notes.

## File Naming

The file names encode the robot configuration:

| Pattern | Meaning |
| --- | --- |
| `left` / `right` | Left-hand or right-hand model |
| `single_left` / `single_right` | Single-arm system with the arm mounted on one side |
| `bimanual` | Dual-arm system |
| `revo2` | Configuration with Revo2 hand attached |
| `revo3` | Configuration with Revo3 hand attached |

Examples:

```text
revoarm_system/urdf/revoarm_single_right_revo3.urdf
revoarm_system/mjcf/revoarm_bimanual_revo2.xml
revoarm_system/usd/revoarm_bimanual_revo3.usd
revotron_system/mjcf/revotron_bimanual_revo3.xml
```

## Using the Models

URDF files can be loaded by common robotics tools such as ROS, RViz, Pinocchio, and other URDF-compatible parsers.

MJCF files can be loaded directly with MuJoCo:

```python
import mujoco

model = mujoco.MjModel.from_xml_path(
    "revoarm_system/mjcf/revoarm_bimanual_revo3.xml"
)
data = mujoco.MjData(model)
```

USD files can be opened with USD-compatible tools such as `usdview` or loaded in NVIDIA Isaac Sim / Isaac Lab:

```bash
usdview revo3_system/usd/revo3_left.usd
```

The top-level USD files, such as `revo3_system/usd/revo3_left.usd`, are the recommended entry points. The `usd/configuration/` files are implementation layers used by the entry point to compose base geometry, physics properties, robot metadata, and optional sensor layers.

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

# BrainCo Robot Description Assets

This repository contains public robot description assets for BrainCo robot hands, arms, and combined arm-hand systems. The package is intended for simulation, visualization, integration testing, and downstream robotics research.

The public release includes description files in both URDF and MJCF formats, together with the mesh assets they reference.

## What Is Included

| System | Description | Formats |
| --- | --- | --- |
| `revo2_system` | Revo2 left and right dexterous hands | URDF, MJCF |
| `revo3_system` | Revo3 left and right dexterous hands | URDF, MJCF |
| `revoarm_system` | Single-arm and bimanual RevoArm assemblies with Revo2/Revo3 hands | URDF, MJCF |
| `revotron_system` | Revotron bimanual platform assemblies | URDF, MJCF |

## Repository Layout

```text
.
├── revo2_system/
│   ├── meshes/
│   ├── urdf/
│   └── mjcf/
├── revo3_system/
│   ├── meshes/
│   ├── urdf/
│   └── mjcf/
├── revoarm_system/
│   ├── meshes/
│   ├── urdf/
│   └── mjcf/
└── revotron_system/
    ├── meshes/
    ├── urdf/
    └── mjcf/
```

Each system directory follows the same convention:

- `urdf/`: URDF robot description files.
- `mjcf/`: MuJoCo XML model files.
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

Mesh paths are stored as relative paths, so load models from the repository root or preserve the directory layout when copying files into another project.

## Notes For Simulation

- MJCF files separate visual and collision geometry where applicable. Visual geoms are intended for rendering, while collision geoms are intended for contact simulation.
- The models are provided as description assets. Controller gains, task-space policies, calibration data, and application-specific simulation settings are intentionally left to downstream projects.

## Work In Progress

The public asset set is still evolving. Planned or ongoing work includes:

- MJCF actuator definitions and control-ready simulation settings.
- USD compatibility and downstream scene-description adaptations.
- Additional validation across common robotics and simulation toolchains.

## License

License information will be provided with the public release. Please review the accompanying license before redistributing or modifying these assets.

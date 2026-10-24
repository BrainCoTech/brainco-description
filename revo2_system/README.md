# revo2_system

> **MJCF and USD must be generated locally since 20261025.**
> This repository ships URDF, assets and conversion tools. From its root, run
> `./convert_all_urdf_to_mjcf.sh` (default: URDF inertia) or
> `./convert_all_urdf_to_usd.sh` (default: flattened USD, requires Isaac Lab / Isaac Sim).
> **客户需要自行生成 MJCF 和 USD。** See [conversion setup](../CONVERSION.md).

Self-contained URDF + mesh bundle.

```
revo2_system/
├── meshes/
│   ├── arm/{visual,collision}/
│   ├── body/{visual,collision}/        # if applicable
│   ├── connector/{visual,collision}/
│   └── hands/{visual,collision}/
└── urdf/
    └── *.urdf
```

URDFs reference meshes via RELATIVE paths (`../meshes/...`), so the
folder is fully self-contained — no ROS package resolution required.
For Revo3 configurations, unsuffixed URDFs have no tactile markers;
`*_mx_touch.urdf` selects MX and `*_mt_touch.urdf` selects MT.
All three variants share the same physical geometry.
RViz / MoveIt / urdfpy / pybullet all resolve relative
`<mesh filename>` against the URDF file's directory.

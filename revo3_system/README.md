# revo3_system

> **Default MJCF and USD must be generated locally since 20261025.**
> This repository ships URDF, assets and conversion tools. From its root, run
> `./convert_all_urdf_to_mjcf.sh` (default: URDF inertia) or
> `./convert_all_urdf_to_usd.sh` (default: flattened USD, requires Isaac Lab / Isaac Sim).
> **客户需要自行生成 MJCF 和 USD。** See [conversion setup](../CONVERSION.md).

An optional [reviewed right-hand collision snapshot (2026-10-27)](optimized/right_20261027/README.md)
is provided separately with ready-to-load MJCF/USD, 144 convex instances and 90 unique meshes.
This snapshot preserves the original visuals and includes integrity checks and validation notes.
It does not change the canonical URDFs or the default conversion workflow.
最新版右手碰撞资产见上述独立目录，包含可直接加载的模型、共享凸包及说明。

Self-contained URDF + mesh bundle.

```
revo3_system/
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

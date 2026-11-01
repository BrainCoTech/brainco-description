# revo3_system

> **Default MJCF and USD must be generated locally since 20261025.**
> This repository ships URDF, assets and conversion tools. From its root, run
> `./convert_all_urdf_to_mjcf.sh` (default: URDF inertia) or
> `./convert_all_urdf_to_usd.sh` (default: flattened USD, requires Isaac Lab / Isaac Sim).
> **客户需要自行生成 MJCF 和 USD。** See [conversion setup](../CONVERSION.md).

An optional [reviewed right-hand collision snapshot (2026-10-27)](optimized/right_20261027/README.md)
is provided separately with ready-to-load MJCF/USD, 144 convex instances and 90 unique meshes.
This snapshot preserves the original visuals and includes integrity checks and validation notes.
On the **dev** branch, `urdf/revo3_right.urdf` now uses these reviewed collision
meshes, with its original visuals, joint origins/axes and inertial definitions preserved.
The right thumb CMR range is **0–105°** (`0–1.8325957145940461 rad`) across
all right-hand variants and RevoArm/RevoTron assemblies.
The right MX/MT, left-hand and arm/platform assembly URDFs retain the old collisions.
See [URDF migration and validation](URDF_COLLISIONS.md) for scope and commands.
`dev` 分支已将审核版碰撞反向写入右手无触觉 URDF；其他变体尚未迁移。

[PACE identified parameters (2026-11-02)](parameters/README.md) include the
`fit_03` baseline, `balanced` candidate, electrical fits, plots and loading examples.
已附上 21 关节辨识参数及加载示例；使用时按关节名称配置执行器。

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
The three variants share the original visual/link structure. On `dev`, their
collision profiles differ until the MX/MT migration is completed.
RViz / MoveIt / urdfpy / pybullet all resolve relative
`<mesh filename>` against the URDF file's directory.

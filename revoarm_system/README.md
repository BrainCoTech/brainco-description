# revoarm_system

Self-contained URDF + mesh bundle.

```
revoarm_system/
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
For Revo3 configurations, `*_mx_touch.urdf` contains the tactile point
links and is the system default. The unsuffixed sibling omits those
points and their fixed joints, preserving the physical geometry.
RViz / MoveIt / urdfpy / pybullet all resolve relative
`<mesh filename>` against the URDF file's directory.

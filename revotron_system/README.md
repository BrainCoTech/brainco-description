# revotron_system

Self-contained URDF + mesh bundle.

```
revotron_system/
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

## Default appearance

All standard Revotron URDF entry points include the approved 2026-09-20
metallic-paint appearance; no CMF-suffixed variant is required. Silver arm/body
shells, dark gray trim, cyan light covers, logos and decorative details are
defined in the source `revotron_description` URDFs and connector xacro.
Visual-only meshes are packaged under `meshes/body/visual/appearance/`.
Original joint, inertial and collision definitions are preserved.

Colors and decorative masking boundaries are display approximations. Standard
URDF does not encode metallic reflectance, actual illumination or optical PC
transparency. The face expression is a static illustration.

MJCF conversion resolves both global and inline URDF colors. Appearance meshes
use shell inertia so surface decals remain loadable in MuJoCo. USD conversion
preserves the visual materials and applies the v4 collision/physics settings.
Conversion code is maintained in the source `robot_system_description/tools/`
and copied to the bundle root by `package_urdf.sh`.

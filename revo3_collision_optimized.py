"""Keep explicit Revo3 convex parts intact when importing a migrated URDF."""

import xml.etree.ElementTree as ET


PREFIX = "revo3_opt_"


def optimized_collision_count(urdf_path):
    return sum((c.get("name") or "").startswith(PREFIX)
               for c in ET.parse(urdf_path).findall(".//collision"))


def configure_optimized_usd(urdf_path, output_path, *, verify_only=False):
    """Author collision settings on mesh prims, including fixed-link mergers.

    The importer can name the container after the URDF collision or mesh file.
    Both names use the reserved prefix. Fail if any explicit part disappeared.
    """
    from pxr import PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics

    expected = optimized_collision_count(urdf_path)
    if not expected:
        return 0
    stage = Usd.Stage.Open(str(output_path))
    paths = []
    for prim in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
        if not prim.IsA(UsdGeom.Mesh):
            continue
        parts = str(prim.GetPath()).split("/")
        if any(p.startswith(PREFIX) for p in parts) and (
            "collisions" in parts or prim.HasAPI(UsdPhysics.CollisionAPI)
        ):
            paths.append(prim.GetPath())
    if len(paths) != expected:
        raise RuntimeError(f"Optimized colliders lost during USD import: {len(paths)} != {expected}")
    if not verify_only:
        # Override per-shape properties without changing mesh coordinates.
        from revo3_collision_v4 import _make_editable
        _make_editable(stage, paths)
        for path in paths:
            prim = stage.GetPrimAtPath(path)
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexHull")
            PhysxSchema.PhysxConvexHullCollisionAPI.Apply(prim).CreateHullVertexLimitAttr(255)
            contact = PhysxSchema.PhysxCollisionAPI.Apply(prim)
            contact.CreateContactOffsetAttr(0.0001)
            contact.CreateRestOffsetAttr(0.0)
            prim.CreateAttribute("newton:maxHullVertices", Sdf.ValueTypeNames.Int, custom=True).Set(-1)
        stage.GetRootLayer().Save()
    for path in paths:
        prim = stage.GetPrimAtPath(path)
        expected_attrs = {
            "physics:collisionEnabled": True,
            "physics:approximation": "convexHull",
            "physxConvexHullCollision:hullVertexLimit": 255,
            "newton:maxHullVertices": -1,
        }
        for name, value in expected_attrs.items():
            if prim.GetAttribute(name).Get() != value:
                raise RuntimeError(f"Optimized collider setting not saved: {path}: {name}")
    print(f"Explicit Revo3 convex hulls verified: {len(paths)}")
    return len(paths)

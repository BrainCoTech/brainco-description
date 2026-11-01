"""Apply the backtrim v4 collision settings to imported Revo3 hands.

Adapted from the v4 package's ``isaaclab_collision_setup.py``. Both hands
are recognized by mesh names, including when fixed links have been merged.
Other robot colliders keep their existing settings.
"""

import math
import re


_HAND_NAME = re.compile(r"^(left|right)_(?:hand|palm|thumb|index|middle|ring|little)_")
_PALM_NAME = re.compile(r"^(left|right)_palm_backtrim_v2$")
_THUMB_NAME = re.compile(r"^cmr_v4_(\d{2})$")
_PALM_ATTRIBUTES = {
    "shrinkWrap": True,
    "minThickness": 0.0001,
    "errorPercentage": 0.01,
    "voxelResolution": 8000000,
    "maxConvexHulls": 32,
    "hullVertexLimit": 128,
}


def _collect(stage, robot_prim_path):
    from pxr import Usd, UsdPhysics

    root = stage.GetPrimAtPath(robot_prim_path) if robot_prim_path else stage.GetPseudoRoot()
    if not root:
        raise ValueError(f"Robot prim does not exist: {robot_prim_path}")
    prims = list(Usd.PrimRange(root, Usd.TraverseInstanceProxies()))
    hands = {}
    for prim in prims:
        if not prim.HasAPI(UsdPhysics.CollisionAPI):
            continue
        # The URDF importer puts meshes below <link>/collisions/<mesh>/... .
        names = []
        parent = prim
        while parent and parent != root and parent.GetName() not in {"collisions", "Geometry"}:
            names.append(parent.GetName())
            parent = parent.GetParent()
        if not parent or parent.GetName() not in {"collisions", "Geometry"}:
            continue
        link = parent.GetParent()
        mesh_side = next((m.group(1) for name in names if (m := _HAND_NAME.match(name))), None)
        link_match = _HAND_NAME.match(link.GetName())
        side = mesh_side or (link_match.group(1) if link_match else None)
        palm = any(_PALM_NAME.fullmatch(name) for name in names)
        thumb = next((m.group(1) for name in names if (m := _THUMB_NAME.fullmatch(name))), None)
        if side is None:
            if thumb is not None:
                raise RuntimeError(f"Cannot identify hand side for {prim.GetPath()}")
            continue
        # Sibling links share a robot container. This separates the same side
        # of different robots while sharing a group for merged hand links.
        # Importer 3 nests links under Geometry; group by the robot root.
        container = parent.GetParent() if parent.GetName() == "Geometry" else link.GetParent()
        key = (container.GetPath(), side)
        hand = hands.setdefault(key, {"colliders": [], "palms": [], "thumbs": []})
        hand["colliders"].append(prim.GetPath())
        if palm:
            hand["palms"].append(prim.GetPath())
        if thumb is not None:
            hand["thumbs"].append((prim.GetPath(), thumb))

    hands = {key: hand for key, hand in hands.items() if hand["palms"] or hand["thumbs"]}
    for (container, side), hand in hands.items():
        if len(hand["palms"]) != 1:
            raise RuntimeError(f"Expected one v4 palm for {container} ({side}), found {len(hand['palms'])}")
        hull_ids = {index for _, index in hand["thumbs"]}
        if len(hand["thumbs"]) != 32 or hull_ids != {f"{i:02d}" for i in range(32)}:
            raise RuntimeError(
                f"Expected 32 distinct v4 thumb hulls (00..31) for {container} ({side}), "
                f"found {len(hand['thumbs'])}: {sorted(hull_ids)}"
            )

    articulations = {
        prim.GetPath()
        for prim in prims
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI)
        and any(prim.GetPath().HasPrefix(container) for container, _ in hands)
    }
    if hands and not articulations:
        raise RuntimeError("Revo3 v4 hand colliders were found, but their articulation root was not found")
    return hands, articulations


def _make_editable(stage, paths):
    # De-instance only ancestors of prims that will receive overrides. Visual
    # geometry can remain instanced. Re-fetch after each change to composition.
    prefixes = {prefix for path in paths for prefix in path.GetPrefixes()}
    for path in sorted(prefixes, key=lambda p: p.pathElementCount):
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsInstance():
            prim.SetInstanceable(False)


def _summary(hands):
    return {
        "hand_count": len(hands),
        "palm_colliders_configured": sum(len(h["palms"]) for h in hands.values()),
        "thumb_hulls_configured": sum(len(h["thumbs"]) for h in hands.values()),
        "contact_colliders_configured": sum(len(h["colliders"]) for h in hands.values()),
    }


def apply_collision_settings(stage, robot_prim_path=None):
    """Apply v4 settings in the current edit target; return configured counts.

    An incomplete v4 hand raises before authoring changes. Stages without v4
    hands are unchanged. Save/export the stage after calling this function.
    """
    hands, articulations = _collect(stage, robot_prim_path)
    if not hands:
        return _summary(hands)

    from pxr import PhysxSchema, UsdPhysics

    _make_editable(stage, list(articulations) + [p for h in hands.values() for p in h["colliders"]])
    for path in articulations:
        PhysxSchema.PhysxArticulationAPI.Apply(stage.GetPrimAtPath(path)).CreateEnabledSelfCollisionsAttr(True)
    for hand in hands.values():
        for path in hand["colliders"]:
            collision = PhysxSchema.PhysxCollisionAPI.Apply(stage.GetPrimAtPath(path))
            collision.CreateContactOffsetAttr(0.0001)
            collision.CreateRestOffsetAttr(0.0)
        for path, _ in hand["thumbs"]:
            UsdPhysics.MeshCollisionAPI.Apply(stage.GetPrimAtPath(path)).CreateApproximationAttr("convexHull")
        for path in hand["palms"]:
            prim = stage.GetPrimAtPath(path)
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexDecomposition")
            fit = PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(prim)
            fit.CreateShrinkWrapAttr(True)
            fit.CreateMinThicknessAttr(0.0001)
            fit.CreateErrorPercentageAttr(0.01)
            fit.CreateVoxelResolutionAttr(8000000)
            fit.CreateMaxConvexHullsAttr(32)
            fit.CreateHullVertexLimitAttr(128)
    return verify_collision_settings(stage, robot_prim_path)


def verify_collision_settings(stage, robot_prim_path=None):
    """Check settings, including after reopening an exported USD; raise on mismatch."""
    hands, articulations = _collect(stage, robot_prim_path)

    def check(path, name, expected):
        actual = stage.GetPrimAtPath(path).GetAttribute(name).Get()
        matches = (
            isinstance(actual, (int, float)) and math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-10)
            if isinstance(expected, float)
            else actual == expected
        )
        if not matches:
            raise RuntimeError(f"{path}: {name} = {actual!r}; expected {expected!r}")

    for path in articulations:
        check(path, "physxArticulation:enabledSelfCollisions", True)
    for hand in hands.values():
        for path in hand["colliders"]:
            check(path, "physxCollision:contactOffset", 0.0001)
            check(path, "physxCollision:restOffset", 0.0)
        for path, _ in hand["thumbs"]:
            check(path, "physics:approximation", "convexHull")
        for path in hand["palms"]:
            check(path, "physics:approximation", "convexDecomposition")
            for name, expected in _PALM_ATTRIBUTES.items():
                check(path, f"physxConvexDecompositionCollision:{name}", expected)
    return _summary(hands)

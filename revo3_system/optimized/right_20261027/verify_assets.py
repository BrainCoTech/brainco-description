"""Check the published Revo3 snapshot. Add --runtime for MuJoCo/USD import checks."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", action="store_true", help="Requires mujoco, numpy and pxr (OpenUSD)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    system = root.parents[1]
    manifest = json.loads((root / "collision_manifest.json").read_text())
    for group in ("meshes", "visual_dependencies", "exports"):
        for name, info in manifest[group].items():
            path = (root / name).resolve()
            require(path.is_relative_to(system), f"Dependency escapes revo3_system: {name}")
            require(path.is_file(), f"Missing dependency: {name}")
            require(path.stat().st_size == info["bytes"], f"Size mismatch: {name}")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"], f"SHA-256 mismatch: {name}")
    vertices = {}
    for name, info in manifest["meshes"].items():
        vertices[name] = sum(line.startswith("v ") for line in (root / name).read_text().splitlines())
        require(vertices[name] == info["vertices"], f"Vertex count mismatch: {name}")
    owners = manifest["owners"]
    require(len(owners) == 22, "Expected 22 collision owners")
    require(sum(len(o["mesh_files"]) for o in owners) == 144, "Expected 144 convex instances")
    require({f for o in owners for f in o["mesh_files"]} == set(vertices), "Mesh ownership mismatch")
    require(len(vertices) == 90 and sum(vertices.values()) == 5427, "Unique geometry count mismatch")
    require(sum(vertices[f] for o in owners for f in o["mesh_files"]) == 9678, "Expanded vertex count mismatch")

    xml = ET.parse(root / "revo3_right.xml").getroot()
    known = set(manifest["meshes"]) | set(manifest["visual_dependencies"])
    for elem in xml.iter():
        if "file" in elem.attrib:
            require(elem.get("file") in known, f"Unlisted MJCF dependency: {elem.get('file')}")
    require(len(xml.findall(".//geom[@class='collision']")) == 144, "MJCF collision count mismatch")

    if args.runtime:
        import mujoco
        import numpy as np
        from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils

        model = mujoco.MjModel.from_xml_path(str(root / "revo3_right.xml"))
        active = np.flatnonzero(model.geom_contype | model.geom_conaffinity)
        meshes = np.unique(model.geom_dataid[active])
        require(len(active) == 144 and model.njnt == 21, "MuJoCo collider/joint count mismatch")
        require(len(meshes) == 90 and model.mesh_vertnum[meshes].sum() == 5427, "MuJoCo shared geometry mismatch")
        stage = Usd.Stage.Open(str(root / "revo3_right.usd"))
        colliders = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)
                     and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()]
        require(len(colliders) == 144, "USD collision count mismatch")
        for prim in colliders:
            require(prim.IsA(UsdGeom.Mesh), f"Collider is not a mesh: {prim.GetPath()}")
            require(UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() == "convexHull", "Unexpected decomposition")
            require(prim.GetAttribute("newton:maxHullVertices").Get() == -1, "Newton hull limit changed")
            require(prim.GetAttribute("physxConvexHullCollision:hullVertexLimit").Get() == 255, "PhysX hull limit changed")
        visuals = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh) and "/visuals/" in str(p.GetPath())]
        require(len(visuals) == 57, "USD visual mesh count mismatch")
        _, assets, unresolved = UsdUtils.ComputeAllDependencies(str(root / "revo3_right.usd"))
        require(set(unresolved) <= {"OmniPBR.mdl"}, f"Unresolved USD dependencies: {unresolved}")
        require(all(Path(p).is_file() for p in assets), "Missing USD assets")
    print("PASS: 144 convex instances, 90 unique meshes, 5427 unique / 9678 expanded vertices.")
    if args.runtime:
        print("PASS: MuJoCo and USD runtime imports, 21 active joints, 57 original visual meshes.")


if __name__ == "__main__":
    main()

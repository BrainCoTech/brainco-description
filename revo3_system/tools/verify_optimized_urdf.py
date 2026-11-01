#!/usr/bin/env python3
"""Check the migrated URDF; --runtime also compares MuJoCo geometry over 129 poses.

Runtime checks require numpy, scipy, mujoco. Neither mode modifies source assets.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

SYSTEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYSTEM.parent))
from urdf_to_mjcf import UrdfModel, build_mjcf
from sync_optimized_collisions import non_collision_tree


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", action="store_true")
    parser.add_argument("--usd", type=Path, help="Also check an Isaac-imported USD (requires --runtime and pxr)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.usd and not args.runtime:
        parser.error("--usd requires --runtime")
    urdf = SYSTEM / "urdf/revo3_right.urdf"
    folder = SYSTEM / "meshes/hands/collision/right/optimized_20261027"
    manifest = json.loads((folder / "collision_manifest.json").read_text())
    root = ET.parse(urdf).getroot()
    instances, expanded_vertices = 0, 0
    used = set()
    actual_owners = {link.get("name"): link for link in root.findall("link") if link.findall("collision")}
    assert set(actual_owners) == {owner["name"] for owner in manifest["owners"]}
    for owner in manifest["owners"]:
        colliders = actual_owners[owner["name"]].findall("collision")
        assert len(colliders) == owner["collision_instances"]
        for collider, filename in zip(colliders, owner["mesh_files"]):
            path = (urdf.parent / collider.find("geometry/mesh").get("filename")).resolve()
            assert path == (folder / filename).resolve()
            assert digest(path) == manifest["mesh_files"][filename]["sha256"]
            used.add(path)
            expanded_vertices += sum(line.startswith("v ") for line in path.read_text().splitlines())
            instances += 1
    stats = dict(collision_instances=instances, unique_meshes=len(used),
                 unique_vertices=sum(sum(line.startswith("v ") for line in p.read_text().splitlines()) for p in used),
                 expanded_vertices=expanded_vertices,
                 collision_owners=len(actual_owners), links=len(root.findall("link")),
                 revolute_joints=len(root.findall("joint[@type='revolute']")),
                 fixed_joints=len(root.findall("joint[@type='fixed']")))
    for key in ("collision_instances", "unique_meshes", "unique_vertices", "expanded_vertices", "collision_owners"):
        assert stats[key] == manifest["statistics"][key], (key, stats[key])
    report = {"urdf_sha256": digest(urdf), "manifest_sha256": digest(folder / "collision_manifest.json"),
              "non_collision_sha256": hashlib.sha256(non_collision_tree(urdf.read_text())).hexdigest(),
              "statistics": stats}
    assert report["non_collision_sha256"] == manifest["non_collision_sha256"]
    report["non_collision_matches_baseline"] = manifest["base_commit"]
    if args.runtime:
        import mujoco
        import numpy as np
        from scipy.spatial import cKDTree

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "revo3_right.xml"
            build_mjcf(UrdfModel(urdf), output).write(output, encoding="unicode")
            candidate = mujoco.MjModel.from_xml_path(str(output))
            reference_path = SYSTEM / "optimized/right_20261027/revo3_right.xml"
            reference = mujoco.MjModel.from_xml_path(str(reference_path))

            def geoms_by_owner_hash(path, model):
                xml = ET.parse(path).getroot()
                meshes = {m.get("name"): digest((path.parent / m.get("file")).resolve())
                          for m in xml.findall("asset/mesh")}
                result = {}
                for body in xml.findall(".//body"):
                    for geom in body.findall("geom"):
                        if geom.get("class") != "collision":
                            continue
                        key = body.get("name"), meshes[geom.get("mesh")]
                        assert key not in result, key
                        result[key] = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom.get("name"))
                return result

            cg, rg = geoms_by_owner_hash(output, candidate), geoms_by_owner_hash(reference_path, reference)
            assert cg.keys() == rg.keys()
            cdata, rdata = mujoco.MjData(candidate), mujoco.MjData(reference)
            ids = np.flatnonzero(candidate.geom_group == 3)
            mids = np.unique(candidate.geom_dataid[ids])
            assert len(ids) == 144 and len(mids) == 90
            assert int(candidate.mesh_vertnum[mids].sum()) == 5427
            assert int(candidate.mesh_vertnum[candidate.geom_dataid[ids]].sum()) == 9678
            rj = [mujoco.mj_name2id(reference, mujoco.mjtObj.mjOBJ_JOINT, candidate.joint(j).name)
                  for j in range(candidate.njnt)]
            assert candidate.njnt == reference.njnt == 21 and min(rj) >= 0
            assert np.allclose(candidate.jnt_range, reference.jnt_range[rj], atol=1e-10)
            rng = np.random.default_rng(20261101)
            poses = np.vstack([np.zeros(candidate.nq), rng.uniform(candidate.jnt_range[:, 0], candidate.jnt_range[:, 1], (128, 21))])
            maximum = 0.0

            def points(model, data, geom):
                mid = model.geom_dataid[geom]
                start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
                return model.mesh_vert[start:start + count] @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]

            for pose in poses:
                cdata.qpos[:] = pose
                for j, target in enumerate(rj):
                    rdata.qpos[reference.jnt_qposadr[target]] = pose[candidate.jnt_qposadr[j]]
                mujoco.mj_forward(candidate, cdata)
                mujoco.mj_forward(reference, rdata)
                assert np.isfinite(cdata.qacc).all()
                for key in cg:
                    a, b = points(candidate, cdata, cg[key]), points(reference, rdata, rg[key])
                    maximum = max(maximum, float(cKDTree(a).query(b)[0].max()), float(cKDTree(b).query(a)[0].max()))
            assert maximum < 2e-7, maximum
            report["mujoco"] = {"version": mujoco.__version__, "poses": len(poses),
                "max_collision_vertex_deviation_m": maximum,
                "collision_instances": len(ids), "unique_meshes": len(mids),
                "unique_vertices": int(candidate.mesh_vertnum[mids].sum()),
                "expanded_vertices": int(candidate.mesh_vertnum[candidate.geom_dataid[ids]].sum()),
                "canonical_urdf_total_link_mass_kg": float(candidate.body_mass.sum()),
                "note": "Geometry equivalence only; snapshot engineering inertias are not copied."}
            if args.usd:
                from pxr import Usd, UsdGeom, UsdPhysics
                stage = Usd.Stage.Open(str(args.usd.resolve()))
                assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
                assert UsdGeom.GetStageUpAxis(stage) == "Z"
                colliders = [p for p in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies())
                             if p.HasAPI(UsdPhysics.CollisionAPI)]
                assert len(colliders) == 144
                cdata.qpos[:] = 0
                mujoco.mj_forward(candidate, cdata)
                by_name = {}
                for owner in manifest["owners"]:
                    for index, filename in enumerate(owner["mesh_files"]):
                        by_name[f"revo3_opt_{owner['name']}_{index:03d}"] = cg[owner["name"], digest(folder / filename)]
                seen, unique, expanded, deviation = set(), set(), 0, 0.0
                for prim in colliders:
                    assert prim.IsA(UsdGeom.Mesh)
                    # The leaf can carry a shared prototype's name; the outer
                    # collision container identifies this URDF instance.
                    name = next(part for part in str(prim.GetPath()).split("/") if part in by_name)
                    assert name not in seen
                    seen.add(name)
                    assert prim.GetAttribute("physics:approximation").Get() == "convexHull"
                    assert prim.GetAttribute("newton:maxHullVertices").Get() == -1
                    assert prim.GetAttribute("physxConvexHullCollision:hullVertexLimit").Get() == 255
                    v = np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get())
                    unique.add((v.shape, v.tobytes()))
                    expanded += len(v)
                    transform = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
                    a = (np.c_[v, np.ones(len(v))] @ transform)[:, :3]
                    b = points(candidate, cdata, by_name[name])
                    deviation = max(deviation, float(cKDTree(a).query(b)[0].max()), float(cKDTree(b).query(a)[0].max()))
                assert seen == by_name.keys() and len(unique) == 90 and expanded == 9678
                assert deviation < 2e-7, deviation
                report["usd"] = {"sha256": digest(args.usd), "collision_instances": len(colliders),
                    "unique_point_arrays": len(unique), "expanded_vertices": expanded,
                    "max_collision_vertex_deviation_m": deviation,
                    "all_approximation_convexHull": True,
                    "physx_hull_vertex_limit": 255, "newton_max_hull_vertices": -1}
    report["passed"] = True
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

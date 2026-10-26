# Revo3 right hand: reviewed collision snapshot (2026-10-27)

这是最新优化的 **Revo3 右手无触觉标记版**：掌胶与指根避让、拇指 CMP/CMR、四指共享碰撞网格均包含在内；可视外观保留原始模型。MJCF 和 USD 可直接加载。

This optional, frozen asset preserves the reviewed simulation model. It is deliberately separate from the default `urdf/` conversion workflow. The three canonical right-hand URDFs, left hand, RevoArm and RevoTron are unchanged. Running the repository's batch converters still produces the canonical URDF assets, not this snapshot.

## Files and loading

| File | Use |
| --- | --- |
| `revo3_right.xml` | MuJoCo MJCF, with shared collision mesh definitions |
| `revo3_right.usd` | Same reviewed asset for Newton and Isaac Lab / PhysX |
| `meshes_compact/` | Only the 90 active convex OBJ files, in metres |
| `visual_support/right_palm_led_link.obj` | Original screen geometry converted from DAE for MJCF |
| `collision_manifest.json` | SHA-256 hashes, owner links, shared-template transforms and dynamics notes |
| `validation/` | Source validation summary and publication-equivalence results |
| `verify_assets.py` | File integrity, dependency and optional runtime checks |

Keep the surrounding `revo3_system/meshes/hands/visual/` directory. MJCF reuses those original visual files; USD embeds the visual geometry and references the existing screen texture. All file references are relative to this checkout. No local training-project files or Git LFS downloads are required. `OmniPBR.mdl` is an Isaac Sim / Omniverse runtime shader, not a missing mesh; headless Newton does not require it.

From the repository root, with Python 3.10 or newer:

```bash
python revo3_system/optimized/right_20261027/verify_assets.py
# In an environment with MuJoCo, NumPy and OpenUSD:
python revo3_system/optimized/right_20261027/verify_assets.py --runtime
```

MuJoCo:

```python
import mujoco
model = mujoco.MjModel.from_xml_path(
    "revo3_system/optimized/right_20261027/revo3_right.xml"
)
```

Newton (the same USD is used by PhysX):

```python
import newton
builder = newton.ModelBuilder()
builder.add_usd(
    "revo3_system/optimized/right_20261027/revo3_right.usd",
    floating=False,
    load_visual_shapes=False,
    load_static_visual_shapes=False,
    enable_self_collisions=True,
)
model = builder.finalize(device="cuda:0")
```

In Isaac Lab, point `UsdFileCfg.usd_path` at the absolute path of `revo3_right.usd`. The default prim is `/revo3_single`. This file is already converted: do not run URDF convex decomposition over it again. Actuators, task poses, scene placement and object dynamics belong to the consuming task.

## Geometry and ownership

| Metric | Count |
| --- | ---: |
| Convex instances / analytic primitives | 144 / 0 |
| Collision owner links | 22 |
| Unique OBJ meshes | 90 |
| Unique / expanded collision vertices | 5,427 / 9,678 |
| Palm convexes / vertices | 42 / 1,790 |
| Original visual meshes / triangles | 57 / 241,252 |
| Active joints | 21 |
| Active OBJ data | 381,728 bytes |

Collision owners are the palm rubber link; thumb CMP, CMR, MCP, PIP and DIP; and each other finger's MPR, MCP, PIP and DIP. The four-finger root called “CMR” during review is named **MPR** in the model. Rubber contact surfaces are incorporated into their parent finger link's geometry. Palm shell/touch, wrist/accessory and separate finger rubber/touch links do not add duplicate colliders.

The four fingers share MPR, MCP, PIP and DIP templates. `template_to_owner` in the manifest is a 4×4 rigid transform using column homogeneous coordinates, with translation in metres. Apply it when reusing an OBJ in another format; changing only the filename loses the correct placement. Owners without a shared template use the identity transform. A count of unique meshes describes distinct geometry, not an unconditional GPU-memory guarantee: importer and solver caching also matter.

Each USD collider is an explicit `convexHull` on the concrete mesh. Newton has `newton:maxHullVertices = -1`; PhysX has `hullVertexLimit = 255`. Shared geometry is authored through internal USD references. The validated hull topology has at most 37 vertices per convex polygon and 14 polygons incident on a vertex.

## Dynamics and validation scope

This snapshot retains the reviewed engineering dynamics, including the palm rubber mass/inertia override (mass **0.03825060230603083 kg**). Those values are recorded in the manifest; they are not a replacement for the canonical URDF mass model. No additional body-pair exclusions were added by the optimization. Parent-body filtering still depends on the backend, so a filtered contact list alone cannot establish geometric clearance.

The last geometry revision locally trimmed palm parts 9, 10, 19 and 41 to clear the index/little MPR motion envelopes while preserving the palm contact roof and inner arc. Direct convex-distance checks bypassed pair filtering. Conservative lower bounds across the checked joint ranges are approximately 0.205 mm at index/little MPR, 3.307/3.180 mm at middle/ring MPR, 1.755 mm at thumb CMP and 0.211 mm at thumb CMR. Internal hinge overlap at other adjacent links may remain intentional.

`validation/source_validation.json` records the reviewed source hashes, palm/front/inner-arc checks, 2,125 root/review poses, 2,000 flexion poses and prior MuJoCo, Newton MuJoCo-Warp and PhysX holding smoke checks (4 environments, 250 control steps, 5 seconds; 50 mm, 80 g rigid cube). Those are bounded checks, not a guarantee for arbitrary policies, all self-collision pairs or 4,096-environment memory use.

`validation/packaging.json` records fresh comparisons after publication-path changes: all source USD content is identical after normalizing dependency paths and the obsolete layer documentation; MJCF content and compiled numeric arrays are identical after rebasing files; Newton-imported collider geometry and placement match. Asset hashes change because paths/documentation change, while visual vertices, normals, faces, collision geometry, joints and physical parameters do not.

Publication imports were checked with MuJoCo 3.12.0, Newton 1.6.1 and OpenUSD 26.8. The prior PhysX smoke check used the local Isaac Lab 3.0.0 / Isaac Sim 6.2 environment; this is not a claim of testing every older simulator version.

## Provenance

The integration base is `BrainCoTech/brainco-description` commit `da568324b86b74538dd1e08479103faa90dd9647`. Original visuals came from commit `6db7e2ed1d864ee0a3ab6ff62d43a303787137f6`; referenced visual bytes were checked against the integration base and are identical. Source and packaged SHA-256 hashes are in the manifest.

This directory is the explicit reviewed-snapshot exception to locally generated default MJCF/USD outputs. Future integration into canonical URDFs must preserve original inertias, transfer each collision's owner transform, retain explicit convex pieces through the converters, and be validated again. Renaming this directory's files or copying its engineering inertias into URDFs does not perform that migration.

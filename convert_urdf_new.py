# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Utility to convert a URDF into USD format (new version with collision type selection).

Shared conversion implementation. Direct execution keeps the legacy defaults;
convert_urdf_v4.py selects the backtrim_v4 export settings.

Unified Robot Description Format (URDF) is an XML file format used in ROS to describe all elements of
a robot. For more information, see: http://wiki.ros.org/urdf

This script uses the URDF importer extension from Isaac Sim (``isaacsim.asset.importer.urdf``) to convert a
URDF asset into USD format. Compared to ``convert_urdf.py``, this script adds the ability to choose the
collision approximation method:

* **convex_hull** (凸包): The collision shape is simplified to a single convex hull per mesh. Faster, less accurate.
* **convex_decomposition** (凸分解): The collision shape is decomposed into smaller convex shapes for a closer fit.
  More accurate collision, typically slower to compute.

Usage example:
  ./isaaclab.sh -p scripts/tools/convert_urdf_new.py \\
      /path/to/robot.urdf \\
      /path/to/output/robot.usd \\
      --collision-type convex_decomposition \\
      --headless

positional arguments:
  input               The path to the input URDF file.
  output              The path to store the USD file.

optional arguments:
  -h, --help                Show this help message and exit
  --collision-type          Collision approximation: convex_hull or convex_decomposition. (default: convex_decomposition)
  --merge-joints            Consolidate links that are connected by fixed joints. (default: False)
  --fix-base                Fix the base to where it is imported. (default: False)
  --flatten                 Flatten the composed USD into a single file and remove generated configuration layers.
  --joint-stiffness         The stiffness of the joint drive. (default: 100.0)
  --joint-damping           The damping of the joint drive. (default: 1.0)
  --joint-target-type       The type of control to use for the joint drive. (default: "position")

"""

import argparse
import contextlib
import copy
import json
import math
import os
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path


def create_parser(v4=False):
    parser = argparse.ArgumentParser(
        description="Convert URDF to USD with backtrim_v4 settings." if v4 else __doc__,
    )
    parser.add_argument("input", help="Input URDF file.")
    parser.add_argument("output", help="Output USD file.")
    parser.add_argument("--batch-manifest", type=Path,
                        help="JSON input/output pairs to convert in one Isaac Sim session.")
    parser.add_argument(
        "--collision-type", default="convex_decomposition",
        choices=["convex_hull", "convex_decomposition"],
        help="Base collision approximation; v4 overrides the trimmed palm and CMR meshes.",
    )
    parser.add_argument("--merge-joints", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--fix-base", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--flatten", action="store_true",
        help="Flatten to one USD and remove generated configuration layers and sidecars.",
    )
    parser.add_argument("--joint-stiffness", type=float, default=None)
    parser.add_argument("--joint-damping", type=float, default=None)
    parser.add_argument("--joint-target-type", default="position", choices=["position", "velocity", "none"])
    if v4:
        parser.add_argument(
            "--collision-only", action="store_true",
            help="Apply v4 collision settings while retaining legacy drive, gravity, solver and fixed-joint defaults.",
        )
    parser.set_defaults(v4=v4, collision_only=False)
    return parser


def run(v4=False):
    from isaaclab.app import AppLauncher

    parser = create_parser(v4=v4)
    AppLauncher.add_app_launcher_args(parser)
    modern_launcher = "--headless" not in parser._option_string_actions
    if modern_launcher:
        parser.add_argument("--headless", action="store_true", help="Run conversion without a window.")
    args = parser.parse_args()
    args.full_v4 = v4 and not args.collision_only
    defaults = {
        "merge_joints": args.full_v4,
        "fix_base": args.full_v4,
        "joint_stiffness": 0.0 if args.full_v4 else 100.0,
        "joint_damping": 0.0 if args.full_v4 else 1.0,
    }
    for name, value in defaults.items():
        if getattr(args, name) is None:
            setattr(args, name, value)
    # Full Kit extension teardown can hang after importing a robot. Use fast
    # shutdown, but pass the conversion result to Kit and flush Python logs.
    app = AppLauncher(args, fast_shutdown=True).app
    exit_code = 0
    try:
        if args.batch_manifest:
            jobs = json.loads(args.batch_manifest.read_text())
            converted = failures = 0
            for index, job in enumerate(jobs, 1):
                print(f"[USD {index}/{len(jobs)}] {job['input']}", flush=True)
                job_args = copy.copy(args)
                job_args.input, job_args.output = job["input"], job["output"]
                try:
                    main(job_args)
                    converted += 1
                except Exception:
                    traceback.print_exc()
                    failures += 1
            print(f"Converted: {converted}\nFailures: {failures}", flush=True)
            exit_code = 1 if failures else 0
        else:
            main(args)
    except KeyboardInterrupt:
        exit_code = 130
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        if modern_launcher:
            app.post_quit(exit_code)
            app.close(exit_code=exit_code)
        else:
            app.app.post_quit(exit_code)
            app.close()
    if exit_code:
        raise SystemExit(exit_code)


def iter_imported_layers(output_path: str):
    output_path = Path(output_path)
    yield output_path

    configuration_dir = output_path.parent / "configuration"
    if configuration_dir.is_dir():
        yield from sorted(configuration_dir.glob(f"{output_path.stem}_*.usd"))


def referenced_layer(source_layer: object, asset_path: str):
    from pxr import Sdf

    if not asset_path:
        return source_layer

    found = Sdf.Layer.FindRelativeToLayer(source_layer, asset_path)
    if found is not None:
        return found

    resolved_path = source_layer.ComputeAbsolutePath(asset_path)
    if not resolved_path:
        return None
    return Sdf.Layer.FindOrOpen(resolved_path)


def reference_target_exists(source_layer: object, reference: object) -> bool:
    if not reference.primPath:
        return True

    target_layer = referenced_layer(source_layer, reference.assetPath)
    if target_layer is None:
        return False
    return target_layer.GetPrimAtPath(reference.primPath) is not None


def prune_unresolved_references(output_path: str) -> int:
    """Remove importer-authored reference arcs whose target prim is absent."""
    from pxr import Sdf

    removed = 0
    for layer_path in iter_imported_layers(output_path):
        layer = Sdf.Layer.FindOrOpen(str(layer_path))
        if layer is None:
            continue

        changed = False
        prim_paths: list[object] = []
        layer.Traverse(Sdf.Path.absoluteRootPath, lambda path: prim_paths.append(path))

        for prim_path in prim_paths:
            spec = layer.GetObjectAtPath(prim_path)
            if not hasattr(spec, "referenceList"):
                continue

            for attr_name in (
                "prependedItems",
                "appendedItems",
                "addedItems",
                "explicitItems",
            ):
                items = list(getattr(spec.referenceList, attr_name))
                if not items:
                    continue

                kept = [
                    reference
                    for reference in items
                    if reference_target_exists(layer, reference)
                ]
                if len(kept) != len(items):
                    setattr(spec.referenceList, attr_name, kept)
                    removed += len(items) - len(kept)
                    changed = True

        if changed:
            layer.Save()

    return removed


def remove_generated_sidecars(output_path: str) -> tuple[int, int]:
    output_path = Path(output_path)
    configuration_dir = output_path.parent / "configuration"

    removed = 0
    if configuration_dir.is_dir():
        for layer_path in sorted(configuration_dir.glob(f"{output_path.stem}_*.usd")):
            layer_path.unlink()
            removed += 1

        with contextlib.suppress(OSError):
            configuration_dir.rmdir()

    removed_sidecars = 0
    for sidecar_path in (
        output_path.parent / ".asset_hash",
        output_path.parent / "config.yaml",
    ):
        if sidecar_path.exists():
            sidecar_path.unlink()
            removed_sidecars += 1

    return removed, removed_sidecars


def flatten_usd(output_path: str, destination: str | None = None) -> tuple[int, int]:
    """Flatten the composed USD stage into a single layer at output_path."""
    from pxr import Usd

    output_path = Path(output_path)
    stage = Usd.Stage.Open(str(output_path))
    if stage is None:
        raise RuntimeError(f"Failed to open USD stage for flattening: {output_path}")

    flattened_layer = stage.Flatten()
    destination = Path(destination) if destination else output_path
    temporary_path = destination.with_name(f"{destination.stem}.flattened.tmp{destination.suffix}")
    if not flattened_layer.Export(str(temporary_path)):
        raise RuntimeError(f"Failed to export flattened USD stage: {temporary_path}")

    os.replace(temporary_path, destination)
    return remove_generated_sidecars(str(output_path))


def configure_v4_usd(output_path: str, full_v4: bool):
    """Persist v4 settings on the robot without creating a simulation world."""
    from pxr import PhysxSchema, Usd, UsdPhysics, UsdShade
    from revo3_collision_v4 import apply_collision_settings

    stage = Usd.Stage.Open(str(output_path))
    if stage is None:
        raise RuntimeError(f"Failed to open converted USD: {output_path}")
    stage.SetEditTarget(stage.GetRootLayer())
    if full_v4:
        # Some importer versions ignore make_instanceable=False. Match the
        # standalone v4 export, including visual geometry and nested instances.
        while instances := [prim for prim in stage.Traverse() if prim.IsInstance()]:
            for prim in instances:
                prim.SetInstanceable(False)
    summary = apply_collision_settings(stage)
    for prim in stage.Traverse():
        if prim.GetRelationship("material:binding").HasAuthoredTargets():
            UsdShade.MaterialBindingAPI.Apply(prim)
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            api = PhysxSchema.PhysxArticulationAPI.Apply(prim)
            api.CreateEnabledSelfCollisionsAttr(True)
            if full_v4:
                api.CreateSolverPositionIterationCountAttr(16)
                api.CreateSolverVelocityIterationCountAttr(4)
        if full_v4 and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr(True)
    stage.GetRootLayer().Save()
    print(f"Applied backtrim_v4 collision settings: {summary}")


def verify_v4_usd(output_path: str, full_v4: bool):
    """Re-read the saved file, including a flattened export, and check settings."""
    from pxr import PhysxSchema, Usd, UsdPhysics
    from revo3_collision_v4 import verify_collision_settings

    stage = Usd.Stage.Open(str(output_path))
    stage.GetRootLayer().Reload()
    summary = verify_collision_settings(stage)
    for prim in stage.Traverse():
        if full_v4 and prim.IsInstance():
            raise RuntimeError(f"v4 export still contains an instance: {prim.GetPath()}")
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            api = PhysxSchema.PhysxArticulationAPI(prim)
            expected = [(api.GetEnabledSelfCollisionsAttr(), True)]
            if full_v4:
                expected.extend([
                    (api.GetSolverPositionIterationCountAttr(), 16),
                    (api.GetSolverVelocityIterationCountAttr(), 4),
                ])
            for attr, value in expected:
                if attr.Get() != value:
                    raise RuntimeError(f"v4 setting not saved: {attr.GetPath()} = {attr.Get()}; expected {value}")
        if full_v4 and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            if PhysxSchema.PhysxRigidBodyAPI(prim).GetDisableGravityAttr().Get() is not True:
                raise RuntimeError(f"v4 disableGravity not saved: {prim.GetPath()}")
    print(f"USD saved and v4 settings verified: {output_path} ({summary})")


def visual_geometry_name(prim):
    """Support importer 2's visuals containers and importer 3's Geometry tree."""
    from pxr import UsdPhysics
    if "/visuals/" in str(prim.GetPath()):
        container = prim
        while container and container.GetParent().GetName() != "visuals":
            container = container.GetParent()
        return container.GetName()
    if "/Geometry/" in str(prim.GetPath()) and not prim.HasAPI(UsdPhysics.CollisionAPI):
        return prim.GetName()
    return None


def configure_visual_textures(urdf_path, output_path):
    """Keep imported screen textures bound to portable packaged image paths."""
    from pxr import Sdf, Tf, Usd, UsdShade

    textures = {}
    for visual in ET.parse(urdf_path).findall(".//visual"):
        texture = visual.find("material/texture")
        mesh = visual.find("geometry/mesh")
        if texture is not None and mesh is not None:
            name = visual.get("name") or Path(mesh.get("filename")).stem
            textures[Tf.MakeValidIdentifier(name)] = (
                Path(urdf_path).parent / texture.get("filename")
            ).resolve()
    if not textures:
        return
    stage = Usd.Stage.Open(str(output_path))
    seen = set()
    for prim in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
        if prim.GetTypeName() != "Mesh":
            continue
        name = visual_geometry_name(prim)
        if name not in textures:
            continue
        texture_path = textures[name]
        if not texture_path.is_file():
            raise FileNotFoundError(texture_path)
        if not prim.GetAttribute("primvars:st").Get():
            raise RuntimeError(f"USD screen has no UV coordinates: {prim.GetPath()}")
        material = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()[0]
        if not material:
            raise RuntimeError(f"USD screen has no bound material: {prim.GetPath()}")
        for shader in Usd.PrimRange(material.GetPrim()):
            for attr_name in ("inputs:diffuse_texture", "inputs:file"):
                attr = shader.GetAttribute(attr_name)
                if attr and attr.GetTypeName() == Sdf.ValueTypeNames.Asset:
                    attr.Set(Sdf.AssetPath(os.path.relpath(texture_path, Path(output_path).parent)))
                    seen.add(name)
    if seen != textures.keys():
        raise RuntimeError(f"USD screen texture bindings missing: {textures.keys() - seen}")
    stage.GetRootLayer().Save()
    print(f"USD textured visuals verified: {len(seen)}; image paths relative to USD")


def verify_visual_materials(urdf_path, output_path):
    """Fail conversion if the importer silently drops an authored URDF color."""
    from collections import defaultdict
    from pxr import Tf, Usd, UsdShade

    robot = ET.parse(urdf_path).getroot()
    palette = {m.get("name"): m.find("color").get("rgba")
               for m in robot.findall("material") if m.find("color") is not None}
    expected = defaultdict(set)
    primitive_colors = set()
    for visual in robot.findall(".//visual"):
        material = visual.find("material")
        color = visual.find("material/color")
        rgba = color.get("rgba") if color is not None else \
            palette.get(material.get("name")) if material is not None else None
        if rgba is None:
            continue
        rgb = tuple(float(v) for v in rgba.split()[:3])
        mesh = visual.find("geometry/mesh")
        if mesh is None:
            primitive_colors.add(rgb)
        else:
            name = visual.get("name") or Path(mesh.get("filename")).stem
            expected[Tf.MakeValidIdentifier(name)].add(rgb)

    stage = Usd.Stage.Open(str(output_path))
    actual = defaultdict(set)
    all_colors = set()
    for prim in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
        if prim.GetTypeName() not in {"Mesh", "Sphere", "Cylinder", "Cube"}:
            continue
        geometry_name = visual_geometry_name(prim)
        if geometry_name is None:
            continue
        binding = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()[0]
        if not binding:
            continue
        for shader in Usd.PrimRange(binding.GetPrim()):
            for name in ["inputs:diffuse_color_constant", "inputs:diffuseColor"]:
                attr = shader.GetAttribute(name)
                color = attr.Get()
                if color is None and attr and attr.GetConnections():
                    source = UsdShade.Input(attr).GetConnectedSource()
                    if source and source[0].GetPrim().GetAttribute("info:id").Get() == "UsdUVTexture":
                        # White modulation of a texture is represented by a connection,
                        # not a constant diffuseColor (importer 3's screen material).
                        texture = source[0].GetPrim()
                        scale = texture.GetAttribute("inputs:scale").Get()
                        bias = texture.GetAttribute("inputs:bias").Get()
                        if bias is None or all(v == 0 for v in bias):
                            color = (scale or (1.0, 1.0, 1.0, 1.0))[:3]
                if color is not None:
                    rgb = tuple(float(v) for v in color)
                    if "/Geometry/" in str(prim.GetPath()) and name == "inputs:diffuseColor":
                        # Importer 3 stores URDF sRGB colors in linear PreviewSurface space.
                        rgb = tuple(12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
                                    for v in rgb)
                    actual[geometry_name].add(rgb)
                    all_colors.add(rgb)

    def matches(color, candidates):
        return any(all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(color, c))
                   for c in candidates)

    for name, colors in expected.items():
        for color in colors:
            if not matches(color, actual[name]):
                raise RuntimeError(f"USD visual color missing or changed: {name}: {color}; found {actual[name]}")
    for color in primitive_colors:
        if not matches(color, all_colors):
            raise RuntimeError(f"USD primitive visual color missing: {color}")
    print(f"USD visual colors verified: {len(expected)} mesh names and {len(primitive_colors)} primitive colors")


def main(args_cli):
    import carb
    import omni.kit.app
    from isaaclab.sim.converters import UrdfConverter, UrdfConverterCfg
    from isaaclab.utils.assets import check_file_path
    from isaaclab.utils.dict import print_dict

    # check valid file path
    urdf_path = args_cli.input
    if not os.path.isabs(urdf_path):
        urdf_path = os.path.abspath(urdf_path)
    if not check_file_path(urdf_path):
        raise ValueError(f"Invalid file path: {urdf_path}")
    # create destination path
    dest_path = args_cli.output
    if not os.path.isabs(dest_path):
        dest_path = os.path.abspath(dest_path)

    from revo3_collision_optimized import optimized_collision_count, configure_optimized_usd
    explicit_hulls = optimized_collision_count(urdf_path)
    # Already decomposed parts must not be approximated/decomposed a second time.
    collision_type = "convex_hull" if explicit_hulls else args_cli.collision_type
    converter_options = {}
    if "collision_type" in UrdfConverterCfg.__dataclass_fields__:
        # Isaac Lab 3 / importer 3 renamed the field and enum values.
        converter_options["collision_type"] = {
            "convex_hull": "Convex Hull", "convex_decomposition": "Convex Decomposition",
        }[collision_type]
        converter_options["merge_mesh"] = False
    else:
        converter_options["collider_type"] = collision_type
    urdf_converter_cfg = UrdfConverterCfg(
        asset_path=urdf_path,
        usd_dir=os.path.dirname(dest_path),
        usd_file_name=os.path.basename(dest_path),
        fix_base=args_cli.fix_base,
        merge_fixed_joints=args_cli.merge_joints,
        force_usd_conversion=True,
        **converter_options,
        joint_drive=UrdfConverterCfg.JointDriveCfg(
            gains=UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                stiffness=args_cli.joint_stiffness,
                damping=args_cli.joint_damping,
            ),
            target_type=args_cli.joint_target_type,
        ),
    )
    if args_cli.v4:
        urdf_converter_cfg.self_collision = True
        urdf_converter_cfg.make_instanceable = False
    if args_cli.full_v4:
        urdf_converter_cfg.link_density = 1000.0

    print("-" * 80)
    print(f"Input URDF file: {urdf_path}")
    print(f"Output USD file: {dest_path}")
    print(f"Collision type:  {collision_type} ({explicit_hulls} explicit Revo3 hulls)")
    print("URDF importer config:")
    print_dict(urdf_converter_cfg.to_dict(), nesting=0)
    print("-" * 80)
    urdf_converter = UrdfConverter(urdf_converter_cfg)
    output_path = urdf_converter.usd_path
    # print output
    print("URDF importer output:")
    print(f"Generated USD file: {urdf_converter.usd_path}")
    removed_references = prune_unresolved_references(urdf_converter.usd_path)
    if removed_references:
        print(f"Pruned unresolved USD references: {removed_references}")
    if args_cli.v4:
        configure_v4_usd(urdf_converter.usd_path, full_v4=args_cli.full_v4)
    if explicit_hulls:
        configure_optimized_usd(urdf_path, urdf_converter.usd_path)
    if args_cli.flatten:
        removed_layers, removed_sidecars = flatten_usd(output_path, dest_path)
        output_path = dest_path
        print(f"Flattened USD file: {output_path}")
        if removed_layers:
            print(f"Removed generated configuration layers: {removed_layers}")
        if removed_sidecars:
            print(f"Removed generated sidecar files: {removed_sidecars}")
    configure_visual_textures(urdf_path, output_path)
    if args_cli.v4:
        verify_v4_usd(output_path, full_v4=args_cli.full_v4)
    verify_visual_materials(urdf_path, output_path)
    if explicit_hulls:
        configure_optimized_usd(urdf_path, output_path, verify_only=True)
    print("-" * 80)
    print("-" * 80)

    # Determine if there is a GUI to update:
    # acquire settings interface
    carb_settings_iface = carb.settings.get_settings()
    # read flag for whether a local GUI is enabled
    local_gui = carb_settings_iface.get("/app/window/enabled")
    # read flag for whether livestreaming GUI is enabled
    livestream_gui = carb_settings_iface.get("/app/livestream/enabled")

    # Simulate scene (if not headless)
    if local_gui or livestream_gui:
        # Open the stage with USD
        import omni.usd
        omni.usd.get_context().open_stage(output_path)
        # Reinitialize the simulation
        app = omni.kit.app.get_app_interface()
        # Run simulation
        with contextlib.suppress(KeyboardInterrupt):
            while app.is_running():
                # perform step
                app.update()


if __name__ == "__main__":
    run()

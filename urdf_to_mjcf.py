#!/usr/bin/env python3
"""Convert a URDF robot to a MuJoCo MJCF model.

The generated MJCF follows the common MuJoCo convention of keeping visual and
collision geoms in the same body:

  - visual mesh geoms use class="visual" and do not participate in contacts
  - collision mesh geoms use class="collision" and participate in contacts

Contact exclusions, tendons, actuators, and primitive collision fitting are left
out intentionally. Meshes and URDF sphere/box/cylinder primitives retain their
visual colors and geometry.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path, help="Input URDF path")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output MJCF path. Defaults to <system>/mjcf/<urdf_stem>.xml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to a mjcf directory next to the urdf directory.",
    )
    parser.add_argument(
        "--inertia-mode",
        choices=("urdf", "collision", "visual"),
        default="urdf",
        help=(
            "urdf: write body inertial from URDF. "
            "collision: ignore URDF inertia tensors and let MuJoCo compute inertia "
            "from collision mesh geoms using URDF link mass. "
            "visual: ignore URDF inertia tensors and let MuJoCo compute inertia "
            "from visual mesh geoms using URDF link mass."
        ),
    )
    return parser.parse_args()


def clean_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return name or "unnamed"


def parse_vec(value: str | None, default: str = "0 0 0") -> list[float]:
    return [float(item) for item in (value or default).split()]


def fmt_num(value: float) -> str:
    if abs(value) < 1e-15:
        value = 0.0
    text = f"{value:.12g}"
    return "0" if text == "-0" else text


def fmt_vec(values: list[float] | tuple[float, ...]) -> str:
    return " ".join(fmt_num(value) for value in values)


def rpy_to_quat(rpy: list[float]) -> tuple[float, float, float, float]:
    """Convert URDF fixed-axis roll/pitch/yaw to MuJoCo wxyz quaternion."""
    roll, pitch, yaw = rpy
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)

    w = cy * cp * cr + sy * sp * sr
    x = cy * cp * sr - sy * sp * cr
    y = sy * cp * sr + cy * sp * cr
    z = sy * cp * cr - cy * sp * sr
    return w, x, y, z


def mesh_path(filename: str, urdf_dir: Path) -> Path:
    if filename.startswith("package://"):
        raise ValueError(f"package:// mesh paths are not supported yet: {filename}")
    return (urdf_dir / filename).resolve()


def dae_to_obj(source: Path, output_dir: Path) -> Path:
    """Convert the triangulated screen DAE to MuJoCo's OBJ format, keeping UVs.

    Source meshes use meters and identity scene transforms. Reject other DAE
    layouts instead of silently changing their geometry.
    """
    root = ET.parse(source).getroot()
    ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    unit = root.find("c:asset/c:unit", ns)
    if unit is not None and float(unit.get("meter", "1")) != 1:
        raise ValueError(f"Unsupported DAE units: {source}")
    for node in root.findall(".//c:visual_scene//c:node", ns):
        if any(node.find(f"c:{tag}", ns) is not None
               for tag in ("matrix", "translate", "rotate", "scale", "lookat", "skew")):
            raise ValueError(f"DAE scene transforms need baking: {source}")
    meshes = root.findall(".//c:geometry/c:mesh", ns)
    if len(meshes) != 1:
        raise ValueError(f"Expected one screen mesh: {source}")
    mesh = meshes[0]
    triangles = mesh.findall("c:triangles", ns)
    if len(triangles) != 1 or mesh.find("c:polylist", ns) is not None:
        raise ValueError(f"Expected one triangulated screen mesh: {source}")
    inputs = {el.get("semantic"): el for el in triangles[0].findall("c:input", ns)}
    vertex_source = inputs["VERTEX"].get("source").removeprefix("#")
    vertices = mesh.find(f"c:vertices[@id='{vertex_source}']/c:input[@semantic='POSITION']", ns)
    refs = {"v": vertices.get("source"), "vt": inputs["TEXCOORD"].get("source")}
    if "NORMAL" in inputs:
        refs["vn"] = inputs["NORMAL"].get("source")
    lines = []
    for prefix, ref in refs.items():
        data = mesh.find(f"c:source[@id='{ref.removeprefix('#')}']", ns)
        accessor = data.find("c:technique_common/c:accessor", ns)
        array_id = accessor.get("source").removeprefix("#")
        values = data.find(f"c:float_array[@id='{array_id}']", ns).text.split()
        stride = int(accessor.get("stride", "1"))
        width = 2 if prefix == "vt" else 3
        offset = int(accessor.get("offset", "0"))
        for i in range(int(accessor.get("count"))):
            start = offset + i * stride
            lines.append(prefix + " " + " ".join(values[start:start + width]))
    indices = [int(v) for v in triangles[0].find("c:p", ns).text.split()]
    stride = max(int(el.get("offset", "0")) for el in inputs.values()) + 1
    if len(indices) != int(triangles[0].get("count")) * 3 * stride:
        raise ValueError(f"Invalid DAE triangle indices: {source}")
    semantics = ["VERTEX", "TEXCOORD"] + (["NORMAL"] if "NORMAL" in inputs else [])
    for i in range(0, len(indices), 3 * stride):
        face = ["/".join(str(indices[j + int(inputs[s].get("offset", "0"))] + 1)
                         for s in semantics) for j in range(i, i + 3 * stride, stride)]
        lines.append("f " + " ".join(face))
    target = output_dir / "meshes" / (source.stem + ".obj")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n")
    return target


def default_output_path(urdf_path: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        if urdf_path.parent.name == "urdf":
            output_dir = urdf_path.parent.parent / "mjcf"
        else:
            output_dir = urdf_path.parent / "mjcf"
    return output_dir / f"{urdf_path.stem}.xml"


def add_origin_attrs(elem: ET.Element, origin: ET.Element | None) -> None:
    if origin is None:
        return
    xyz = parse_vec(origin.get("xyz"), "0 0 0")
    rpy = parse_vec(origin.get("rpy"), "0 0 0")
    if any(abs(value) > 1e-15 for value in xyz):
        elem.set("pos", fmt_vec(xyz))
    if any(abs(value) > 1e-15 for value in rpy):
        elem.set("quat", fmt_vec(rpy_to_quat(rpy)))


def link_mass(link_elem: ET.Element) -> float:
    inertial = link_elem.find("inertial") or link_elem
    mass_elem = inertial.find("mass")
    if mass_elem is None:
        return 0.0
    return float(mass_elem.get("value", "0"))


def add_inertial(body_elem: ET.Element, link_elem: ET.Element) -> None:
    inertial = link_elem.find("inertial") or link_elem
    if inertial is link_elem and inertial.find("mass") is None:
        return

    mass_elem = inertial.find("mass")
    inertia_elem = inertial.find("inertia")
    if mass_elem is None or inertia_elem is None:
        return

    mass = link_mass(link_elem)
    if mass <= 0:
        return

    ixx = float(inertia_elem.get("ixx", "0"))
    iyy = float(inertia_elem.get("iyy", "0"))
    izz = float(inertia_elem.get("izz", "0"))
    ixy = float(inertia_elem.get("ixy", "0"))
    ixz = float(inertia_elem.get("ixz", "0"))
    iyz = float(inertia_elem.get("iyz", "0"))
    if ixx <= 0 or iyy <= 0 or izz <= 0:
        return

    mj_inertial = ET.SubElement(body_elem, "inertial")
    mj_inertial.set("mass", fmt_num(mass))

    origin = inertial.find("origin")
    xyz = parse_vec(origin.get("xyz") if origin is not None else None, "0 0 0")
    rpy = parse_vec(origin.get("rpy") if origin is not None else None, "0 0 0")
    mj_inertial.set("pos", fmt_vec(xyz))
    if any(abs(value) > 1e-15 for value in rpy):
        mj_inertial.set("quat", fmt_vec(rpy_to_quat(rpy)))

    if any(abs(value) > 1e-15 for value in (ixy, ixz, iyz)):
        mj_inertial.set("fullinertia", fmt_vec([ixx, iyy, izz, ixy, ixz, iyz]))
    else:
        mj_inertial.set("diaginertia", fmt_vec([ixx, iyy, izz]))


def add_minimal_inertial(body_elem: ET.Element, link_elem: ET.Element) -> None:
    mass = link_mass(link_elem)
    if mass <= 0:
        return

    inertial = link_elem.find("inertial") or link_elem
    origin = inertial.find("origin")
    xyz = parse_vec(origin.get("xyz") if origin is not None else None, "0 0 0")
    tiny_inertia = max(mass * 1e-6, 1e-9)

    mj_inertial = ET.SubElement(body_elem, "inertial")
    mj_inertial.set("mass", fmt_num(mass))
    mj_inertial.set("pos", fmt_vec(xyz))
    mj_inertial.set("diaginertia", fmt_vec([tiny_inertia, tiny_inertia, tiny_inertia]))


def add_joint(body_elem: ET.Element, joint_elem: ET.Element) -> None:
    joint_type = joint_elem.get("type", "fixed")
    if joint_type == "fixed":
        return
    if joint_type not in {"revolute", "continuous", "prismatic"}:
        raise ValueError(f"Unsupported joint type: {joint_type}")

    mj_joint = ET.SubElement(body_elem, "joint")
    mj_joint.set("name", joint_elem.get("name", "joint"))
    mj_joint.set("type", "slide" if joint_type == "prismatic" else "hinge")

    axis = joint_elem.find("axis")
    mj_joint.set("axis", axis.get("xyz", "1 0 0") if axis is not None else "1 0 0")

    limit = joint_elem.find("limit")
    if joint_type != "continuous" and limit is not None:
        lower = limit.get("lower")
        upper = limit.get("upper")
        if lower is not None and upper is not None:
            mj_joint.set("range", f"{fmt_num(float(lower))} {fmt_num(float(upper))}")
        effort = limit.get("effort")
        if effort is not None:
            value = abs(float(effort))
            if value > 0:
                mj_joint.set("actuatorfrcrange", f"{fmt_num(-value)} {fmt_num(value)}")

    dynamics = joint_elem.find("dynamics")
    if dynamics is not None:
        damping = dynamics.get("damping")
        friction = dynamics.get("friction")
        if damping is not None:
            mj_joint.set("damping", fmt_num(float(damping)))
        if friction is not None:
            mj_joint.set("frictionloss", fmt_num(float(friction)))


def collect_mesh_geoms(
    link_elem: ET.Element,
    kind: str,
    urdf_dir: Path,
    output_dir: Path,
    assets: ET.Element,
    used_mesh_names: set[str],
    mesh_cache: dict[tuple, str],
    geom_mass: float | None = None,
    materials: dict[str, str] | None = None,
) -> list[ET.Element]:
    geoms: list[ET.Element] = []

    for index, geom_source in enumerate(link_elem.findall(kind)):
        geometry = geom_source.find("geometry")
        if geometry is None:
            continue
        mesh = geometry.find("mesh")
        link_name = clean_name(link_elem.get("name", "link"))
        geom = ET.Element("geom")
        geom.set("name", clean_name(f"{link_name}_{kind}_{index}"))
        geom.set("class", "visual" if kind == "visual" else "collision")
        if mesh is not None:
            filename = mesh.get("filename")
            if not filename:
                continue
            source_path = mesh_path(filename, urdf_dir)
            if source_path.suffix.lower() == ".dae":
                source_path = dae_to_obj(source_path, output_dir)
            rel_path = os.path.relpath(source_path, output_dir)
            base_name = clean_name(source_path.stem)
            # Geometry is shared; each geom still carries its own origin/material.
            # Keep visual and collision assets separate (inertia/hull semantics).
            scale = tuple(parse_vec(mesh.get("scale"), "1 1 1"))
            cache_key = (source_path, scale, kind)
            mesh_name = mesh_cache.get(cache_key)
            if mesh_name is None:
                mesh_name = clean_name(f"{link_name}_{kind}_{index}_{base_name}")
                while mesh_name in used_mesh_names:
                    mesh_name = f"{mesh_name}_{len(used_mesh_names)}"
                used_mesh_names.add(mesh_name)
                mesh_cache[cache_key] = mesh_name
                asset = ET.SubElement(assets, "mesh", name=mesh_name, file=rel_path)
                if kind == "visual" and "appearance" in source_path.parts:
                    # Surface decals have no enclosed volume.
                    asset.set("inertia", "shell")
                if kind == "collision":
                    asset.set("maxhullvert", "-1")
                if mesh.get("scale") is not None:
                    asset.set("scale", mesh.get("scale"))
            geom.set("mesh", mesh_name)
        elif geometry.find("sphere") is not None:
            geom.set("type", "sphere")
            geom.set("size", geometry.find("sphere").get("radius"))
        elif geometry.find("box") is not None:
            geom.set("type", "box")
            geom.set("size", fmt_vec([v/2 for v in parse_vec(geometry.find("box").get("size"))]))
        elif geometry.find("cylinder") is not None:
            cylinder = geometry.find("cylinder")
            geom.set("type", "cylinder")
            geom.set("size", fmt_vec([float(cylinder.get("radius")), float(cylinder.get("length"))/2]))
        else:
            raise ValueError(f"Unsupported URDF geometry: {link_name}/{kind}/{index}")
        if geom_mass is not None:
            geom.set("mass", fmt_num(geom_mass))
        add_origin_attrs(geom, geom_source.find("origin"))

        color = geom_source.find("material/color")
        if kind == "visual" and color is not None and color.get("rgba"):
            geom.set("rgba", color.get("rgba", "1 1 1 1"))
        elif kind == "visual":
            material = geom_source.find("material")
            name = material.get("name") if material is not None else None
            if name and materials and name in materials:
                geom.set("rgba", materials[name])

        texture = geom_source.find("material/texture")
        if kind == "visual" and texture is not None:
            texture_path = mesh_path(texture.get("filename"), urdf_dir)
            if not texture_path.is_file():
                raise FileNotFoundError(texture_path)
            texture_name = geom.get("name") + "_texture"
            material_name = geom.get("name") + "_material"
            ET.SubElement(assets, "texture", name=texture_name, type="2d",
                          file=os.path.relpath(texture_path, output_dir))
            ET.SubElement(assets, "material", name=material_name, texture=texture_name,
                          rgba=geom.get("rgba", "1 1 1 1"))
            geom.set("material", material_name)

        geoms.append(geom)

    return geoms


def mesh_geom_count(link_elem: ET.Element, kind: str) -> int:
    count = 0
    for geom_source in link_elem.findall(kind):
        if geom_source.find("geometry") is not None:
            count += 1
    return count


class UrdfModel:
    def __init__(self, urdf_path: Path):
        self.urdf_path = urdf_path.resolve()
        self.urdf_dir = self.urdf_path.parent
        self.root = ET.parse(self.urdf_path).getroot()
        self.materials = {
            material.get("name"): material.find("color").get("rgba")
            for material in self.root.findall("material")
            if material.find("color") is not None
        }
        self.links = {link.get("name"): link for link in self.root.findall("link")}
        self.child_joints: dict[str, list[ET.Element]] = defaultdict(list)
        self.parent_by_child: dict[str, str] = {}

        for joint in self.root.findall("joint"):
            parent = joint.find("parent")
            child = joint.find("child")
            if parent is None or child is None:
                continue
            parent_name = parent.get("link")
            child_name = child.get("link")
            if not parent_name or not child_name:
                continue
            self.child_joints[parent_name].append(joint)
            self.parent_by_child[child_name] = parent_name

    @property
    def name(self) -> str:
        return self.root.get("name", self.urdf_path.stem)

    def root_links(self) -> list[str]:
        roots = [name for name in self.links if name not in self.parent_by_child]
        return roots or list(self.links)[:1]


def build_mjcf(model: UrdfModel, output_path: Path, inertia_mode: str = "urdf") -> ET.ElementTree:
    output_dir = output_path.parent.resolve()
    mujoco = ET.Element("mujoco", model=model.name)

    compiler_attrs = {
        "angle": "radian",
        "autolimits": "true",
        "balanceinertia": "true",
    }
    if inertia_mode in {"collision", "visual"}:
        compiler_attrs["inertiafromgeom"] = "true"
    ET.SubElement(mujoco, "compiler", **compiler_attrs)
    ET.SubElement(mujoco, "option", cone="elliptic", impratio="10")

    defaults = ET.SubElement(mujoco, "default")
    visual_default = ET.SubElement(defaults, "default", {"class": "visual"})
    ET.SubElement(
        visual_default,
        "geom",
        type="mesh",
        contype="0",
        conaffinity="0",
        group="2",
    )
    collision_default = ET.SubElement(defaults, "default", {"class": "collision"})
    ET.SubElement(collision_default, "geom", type="mesh", group="3")

    if inertia_mode in {"collision", "visual"}:
        visual_default.find("geom").set("mass", "0")
        collision_default.find("geom").set("mass", "0")

    assets = ET.SubElement(mujoco, "asset")
    worldbody = ET.SubElement(mujoco, "worldbody")
    used_mesh_names: set[str] = set()
    mesh_cache: dict[tuple, str] = {}

    def emit_link(parent_elem: ET.Element, link_name: str, incoming_joint: ET.Element | None) -> None:
        link = model.links[link_name]
        if incoming_joint is None and link_name == "world" and not list(link):
            body_parent = parent_elem
        else:
            body = ET.SubElement(parent_elem, "body", name=link_name)
            if incoming_joint is not None:
                add_origin_attrs(body, incoming_joint.find("origin"))
            if inertia_mode == "urdf":
                add_inertial(body, link)
            if incoming_joint is not None:
                add_joint(body, incoming_joint)

            if (incoming_joint is not None
                    and incoming_joint.get("type") != "fixed"
                    and link_mass(link) <= 0
                    and not link.findall("visual") and not link.findall("collision")
                    and not model.child_joints.get(link_name)):
                # Bare RevoArm link7 is an actuated, massless terminal frame.
                # MuJoCo requires positive inertia even for this empty body.
                # Retain the URDF joint and leave source physical data unchanged.
                body.append(ET.Comment(" Minimum MJCF inertia for a massless terminal frame. "))
                ET.SubElement(body, "inertial", mass="1e-6", pos="0 0 0",
                              diaginertia="1e-9 1e-9 1e-9")

            visual_count = mesh_geom_count(link, "visual")
            collision_count = mesh_geom_count(link, "collision")
            mass = link_mass(link)
            visual_geom_mass = None
            collision_geom_mass = None
            if inertia_mode == "collision" and collision_count > 0 and mass > 0:
                collision_geom_mass = mass / collision_count
            elif inertia_mode == "collision" and collision_count == 0 and mass > 0:
                add_minimal_inertial(body, link)
            elif inertia_mode == "visual" and visual_count > 0 and mass > 0:
                visual_geom_mass = mass / visual_count
            elif inertia_mode == "visual" and visual_count == 0 and mass > 0:
                add_minimal_inertial(body, link)

            for geom in collect_mesh_geoms(
                link,
                "visual",
                model.urdf_dir,
                output_dir,
                assets,
                used_mesh_names,
                mesh_cache,
                materials=model.materials,
                geom_mass=visual_geom_mass
                if inertia_mode == "visual"
                else 0.0
                if inertia_mode == "collision"
                else None,
            ):
                body.append(geom)
            for geom in collect_mesh_geoms(
                link,
                "collision",
                model.urdf_dir,
                output_dir,
                assets,
                used_mesh_names,
                mesh_cache,
                materials=model.materials,
                geom_mass=0.0 if inertia_mode == "visual" else collision_geom_mass,
            ):
                body.append(geom)
            body_parent = body

        for child_joint in model.child_joints.get(link_name, []):
            child = child_joint.find("child")
            if child is not None and child.get("link") in model.links:
                emit_link(body_parent, child.get("link"), child_joint)

    for root_link in model.root_links():
        emit_link(worldbody, root_link, None)

    ET.indent(ET.ElementTree(mujoco), space="  ")
    return ET.ElementTree(mujoco)


def main() -> int:
    args = parse_args()
    urdf_path = args.urdf.expanduser().resolve()
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF not found: {urdf_path}")

    output_path = args.output.expanduser() if args.output else default_output_path(
        urdf_path,
        args.output_dir.expanduser() if args.output_dir else None,
    )
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = UrdfModel(urdf_path)
    tree = build_mjcf(model, output_path, inertia_mode=args.inertia_mode)
    tree.write(output_path, encoding="unicode", xml_declaration=True)
    print(f"Saved MJCF to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

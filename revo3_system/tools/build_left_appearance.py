#!/usr/bin/env python3
"""Build the left-hand CMF variant from the current left-hand URDF.

Requires numpy and trimesh. Run from any directory. Only new appearance assets
are written; source URDF/STLs and all physical properties are preserved.
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "urdf/revo3_left.urdf"
TARGET = ROOT / "urdf/revo3_left_appearance.urdf"
OUTPUT = ROOT / "meshes/hands/visual/left_appearance"
PALETTE = {
    "revo3_white_pc": "0.94 0.95 0.97 1",
    "revo3_aluminum": "0.72 0.74 0.78 1",
    "revo3_polished_aluminum": "0.86 0.88 0.92 1",
    # Visual estimate from the supplied image, NOT a calibrated Pantone value.
    "revo3_silicone_2162u_approx": "0.52 0.54 0.60 1",
}
METAL = "revo3_aluminum"
POLISHED = "revo3_polished_aluminum"
SILICONE = "revo3_silicone_2162u_approx"
WHITE = "revo3_white_pc"


def split_polygon(polygon, axis, boundary, sign):
    """Split on a plane, preserving winding and surface position."""
    inside, outside = [], []
    normal = np.eye(3)[axis] if isinstance(axis, int) else np.asarray(axis)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        da = sign * (a @ normal - boundary)
        db = sign * (b @ normal - boundary)
        (inside if da >= 0 else outside).append(a)
        if (da >= 0) != (db >= 0):
            point = a + (b - a) * da / (da - db)
            inside.append(point)
            outside.append(point)
    return np.asarray(inside), np.asarray(outside)


def paint_region(polygons, planes):
    selected, remainder = [], []
    for polygon in polygons:
        for axis, boundary, sign in planes:
            polygon, rejected = split_polygon(polygon, axis, boundary, sign)
            if len(rejected) >= 3:
                remainder.append(rejected)
            if len(polygon) < 3:
                break
        if len(polygon) >= 3:
            selected.append(polygon)
    return selected, remainder


def triangulate(polygons):
    return np.asarray([
        [p[0], p[i], p[i + 1]]
        for p in polygons for i in range(1, len(p) - 1)
    ])


def partition(mesh, stem):
    """Use existing component seams where available; clip fused CMF regions."""
    groups = defaultdict(list)
    if stem == "base_link":
        # +X is the palm; -X is the dorsum. The wrist stays aluminum.
        white, rest = paint_region(mesh.triangles, [(0, -0.015, -1), (2, 0.018, 1)])
        # The palm tapers toward the fingers, so follow it with a sloping plane.
        silicone, metal = paint_region(rest, [((1, 0, 0.15), 0.0205, 1), (2, 0.025, 1), (2, 0.105, -1)])
        return {WHITE: triangulate(white), SILICONE: triangulate(silicone), METAL: triangulate(metal)}
    if stem == "left_thumb_MCP_Link":
        # The thumb's local +Z points toward the palm contact surface.
        silicone, metal = paint_region(mesh.triangles, [(2, 0.002, 1), (1, -0.010, -1), (1, -0.037, 1)])
        return {SILICONE: triangulate(silicone), METAL: triangulate(metal)}
    if "_DIP_" in stem:
        # The sharp seam separates the rounded silicone cap from its metal tongue.
        adjacency = mesh.face_adjacency[mesh.face_adjacency_angles < np.deg2rad(35)]
        surfaces = trimesh.graph.connected_components(
            adjacency, nodes=np.arange(len(mesh.faces)), min_len=1
        )
        for surface in surfaces:
            triangles = mesh.triangles[surface]
            if "thumb" in stem:
                material = SILICONE if len(surface) > 1500 else METAL
            elif len(surface) > 2000:
                material = SILICONE
            else:
                material = POLISHED if np.ptp(triangles[:, :, 2]) < 0.016 else METAL
            groups[material].extend(triangles)
        return {material: np.asarray(triangles) for material, triangles in groups.items()}

    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1
    )
    if stem == "left_thumb_PIP_Link":
        pad = max(components, key=lambda c: mesh.triangles_center[c, 2].mean())
    elif "_MCP_" in stem or "_PIP_" in stem:
        pad = max(components, key=lambda c: mesh.triangles_center[c, 0].mean())
    else:
        pad = None
    for component in components:
        material = METAL
        triangles = mesh.triangles[component]
        if component is pad:
            material = SILICONE
        elif "_PIP_" in stem and "thumb" not in stem and np.ptp(triangles[:, :, 2]) < 0.016:
            material = POLISHED
        groups[material].extend(triangles)
    return {material: np.asarray(triangles) for material, triangles in groups.items()}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(SOURCE)
    robot = tree.getroot()
    robot.set("name", "revo3_left_appearance")
    robot.insert(0, ET.Comment(
        " Left-hand CMF variant. Colors approximate the supplied design reference. "
        "Standard URDF cannot encode anodizing, roughness, metallic or silicone hardness. "
        "Fused palm/thumb surfaces use approximate material boundaries; see revo3_left_appearance.md. "
    ))
    for index, (name, rgba) in enumerate(PALETTE.items(), 1):
        material = ET.Element("material", name=name)
        ET.SubElement(material, "color", rgba=rgba)
        robot.insert(index, material)

    for link in robot.findall("link"):
        for visual in list(link.findall("visual")):
            source_mesh = visual.find("geometry/mesh")
            path = (SOURCE.parent / source_mesh.get("filename")).resolve()
            stem = path.stem
            # These links consist entirely of metal and reuse the source mesh.
            if any(token in stem for token in ("_MPR_", "_CMP_", "_CMR_")):
                visual.remove(visual.find("material"))
                ET.SubElement(visual, "material", name=METAL)
                continue
            mesh = trimesh.load_mesh(path, process=False)
            mesh.merge_vertices()
            partitions = partition(mesh, stem)
            index = list(link).index(visual)
            link.remove(visual)
            area = 0.0
            for material, triangles in partitions.items():
                part = trimesh.Trimesh(
                    vertices=triangles.reshape(-1, 3),
                    faces=np.arange(len(triangles) * 3).reshape(-1, 3),
                    process=False,
                )
                area += part.area
                filename = f"{stem}__{material.removeprefix('revo3_')}.stl"
                part.export(OUTPUT / filename)
                replacement = deepcopy(visual)
                replacement.set("name", f"{link.get('name')}__{material}")
                replacement.find("geometry/mesh").set(
                    "filename", f"../meshes/hands/visual/left_appearance/{filename}"
                )
                replacement.remove(replacement.find("material"))
                ET.SubElement(replacement, "material", name=material)
                link.insert(index, replacement)
                index += 1
            # Splitting changes tessellation, not the shape or surface area.
            assert np.isclose(area, mesh.area, rtol=1e-9, atol=1e-12), stem
    ET.indent(tree, space="  ")
    tree.write(TARGET, encoding="utf-8", xml_declaration=True)
    print(TARGET)


if __name__ == "__main__":
    main()

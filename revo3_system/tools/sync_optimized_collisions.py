#!/usr/bin/env python3
"""Write the reviewed collision meshes back to the non-tactile right-hand URDF.

Uses only the standard library. Keeps every byte outside <collision> elements;
the snapshot's engineering inertia overrides are deliberately not imported.
"""

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET


SYSTEM = Path(__file__).resolve().parents[1]
SNAPSHOT = SYSTEM / "optimized/right_20261027"
DESTINATION = SYSTEM / "meshes/hands/collision/right/optimized_20261027"
URDF = SYSTEM / "urdf/revo3_right.urdf"
BASE_COMMIT = "9a5b7de899eb7f14e72c69e53e38a0d2fe27ea5a"
NON_COLLISION_SHA256 = "bb82c1bc57af256884220a543f9eece0c46617255f228bf83d3ce8c866ee27b6"


def matrix_to_rpy(matrix):
    """URDF extrinsic XYZ: R = Rz(yaw) Ry(pitch) Rx(roll)."""
    pitch = math.atan2(-matrix[2][0], math.hypot(matrix[0][0], matrix[1][0]))
    if abs(math.cos(pitch)) > 1e-10:
        roll = math.atan2(matrix[2][1], matrix[2][2])
        yaw = math.atan2(matrix[1][0], matrix[0][0])
    else:
        roll = math.atan2(-matrix[1][2], matrix[1][1])
        yaw = 0.0
    return roll, pitch, yaw


def non_collision_tree(text):
    root = ET.fromstring(text)
    for link in root.findall("link"):
        for collision in link.findall("collision"):
            link.remove(collision)
    # Ignore indentation when checking the complete remaining XML structure.
    for elem in root.iter():
        if elem.text is not None and not elem.text.strip():
            elem.text = None
        elem.tail = None
    return ET.tostring(root)


def main():
    source = json.loads((SNAPSHOT / "collision_manifest.json").read_text())
    manifest = {
        "schema_version": 1,
        "profile": source["profile"],
        "source": "revo3_system/optimized/right_20261027/collision_manifest.json",
        "base_commit": BASE_COMMIT,
        "non_collision_sha256": NON_COLLISION_SHA256,
        "units": source["units"],
        "coordinate_convention": source["coordinate_convention"],
        "statistics": source["statistics"],
        "owners": copy.deepcopy(source["owners"]),
        "mesh_files": {},
    }
    original = URDF.read_text()
    if hashlib.sha256(non_collision_tree(original)).hexdigest() != NON_COLLISION_SHA256:
        raise ValueError("URDF visuals/joints/inertia differ from the reviewed migration baseline")
    root = ET.fromstring(original)
    links = {link.get("name") for link in root.findall("link")}
    expected = {owner["name"] for owner in manifest["owners"]}
    if not expected <= links or len(root.findall("joint[@type='revolute']")) != 21:
        raise ValueError("Unexpected right-hand structure; do not transfer by name alone")
    replacements = {}
    for owner in manifest["owners"]:
        matrix = owner["template_to_owner"]
        xyz = [row[3] for row in matrix[:3]] if matrix else [0, 0, 0]
        rpy = matrix_to_rpy(matrix) if matrix else [0, 0, 0]
        fmt = lambda values: " ".join(f"{value:.17g}" for value in values)
        elements, files = [], []
        for index, source_rel in enumerate(owner["mesh_files"]):
            source_file = SNAPSHOT / source_rel
            relative = Path(source_rel).relative_to("meshes_compact")
            relative = relative.with_name(f"revo3_opt_{relative.parent.name}_{relative.stem}.obj")
            target = DESTINATION / relative
            data = source_file.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != source["meshes"][source_rel]["sha256"]:
                raise ValueError(f"Snapshot mesh checksum failed: {source_file}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, target)
            files.append(relative.as_posix())
            manifest["mesh_files"][relative.as_posix()] = {
                "sha256": digest,
                "vertices": sum(line.startswith(b"v ") for line in data.splitlines()),
                "bytes": len(data),
            }
            collision = ET.Element("collision", name=f"revo3_opt_{owner['name']}_{index:03d}")
            ET.SubElement(collision, "origin", xyz=fmt(xyz), rpy=fmt(rpy))
            ET.SubElement(ET.SubElement(collision, "geometry"), "mesh",
                          filename=os.path.relpath(target, URDF.parent))
            ET.indent(collision, space="  ", level=2)
            elements.append("    " + ET.tostring(collision, encoding="unicode"))
        owner["mesh_files"] = files
        replacements[owner["name"]] = "\n".join(elements)

    seen = set()

    def rewrite_link(match):
        block, name = match.group(0), match.group(1)
        # Strip old colliders from every link, including fixed rubber/touch links.
        block = re.sub(r"\n[ \t]*<collision\b[^>]*>.*?</collision>", "", block, flags=re.S)
        if name in replacements:
            seen.add(name)
            block = block.replace("\n  </link>", "\n" + replacements[name] + "\n  </link>")
        return block

    result = re.sub(r'<link name="([^"]+)"\s*>.*?</link>', rewrite_link, original, flags=re.S)
    if seen != expected or non_collision_tree(result) != non_collision_tree(original):
        raise RuntimeError("Collision migration changed non-collision data or missed an owner")
    if len(ET.fromstring(result).findall(".//collision")) != 144:
        raise RuntimeError("Expected exactly 144 collision instances")
    URDF.write_text(result)
    (DESTINATION / "collision_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Updated revo3_right.urdf: 144 convex instances, 90 meshes; visuals/joints/inertia preserved")


if __name__ == "__main__":
    main()

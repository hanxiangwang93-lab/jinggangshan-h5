"""
Maya - Auto-Separate Touching Meshes into Layers
=================================================
Run in Maya Script Editor (Python).

Rule: if two objects TOUCH (bounding boxes intersect), they go to
DIFFERENT layers. Non-touching objects may share a layer.

Uses greedy graph coloring to minimize the number of layers.
"""

import maya.cmds as cmds
from collections import defaultdict

# === Settings ===
PADDING = 0.01  # extra margin for touch test (cm). Increase if "almost touching" should count


def get_world_bbox(transform):
    """Return world-space bounding box [xmin, ymin, zmin, xmax, ymax, zmax]."""
    try:
        return cmds.xform(transform, q=True, ws=True, boundingBox=True)
    except:
        return None


def bboxes_touch(bb1, bb2, padding):
    """Check if two bounding boxes touch/intersect (with optional padding)."""
    # Expand bb1 by padding on all sides
    xmin1, ymin1, zmin1, xmax1, ymax1, zmax1 = bb1
    xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = bb2

    xmin1 -= padding
    ymin1 -= padding
    zmin1 -= padding
    xmax1 += padding
    ymax1 += padding
    zmax1 += padding

    # Check overlap on each axis
    if xmax1 < xmin2 or xmax2 < xmin1:
        return False
    if ymax1 < ymin2 or ymax2 < ymin1:
        return False
    if zmax1 < zmin2 or zmax2 < zmin1:
        return False
    return True


def greedy_graph_coloring(meshes, bboxes, padding):
    """
    Build adjacency graph (edge = objects touch).
    Greedy color: for each object, pick the lowest color not used by neighbors.
    Returns dict: mesh -> color_index
    """
    n = len(meshes)

    # Build adjacency list
    print(f"  Building adjacency for {n} objects...")
    neighbors = defaultdict(list)
    for i in range(n):
        for j in range(i + 1, n):
            if bboxes_touch(bboxes[i], bboxes[j], padding):
                neighbors[i].append(j)
                neighbors[j].append(i)

    edge_count = sum(len(v) for v in neighbors.values()) // 2
    print(f"  {edge_count} touching pairs found")

    # Greedy coloring (Welsh-Powell: sort by degree descending)
    order = sorted(range(n), key=lambda x: len(neighbors[x]), reverse=True)
    colors = {}  # mesh_index -> color

    for idx in order:
        # Find colors used by neighbors
        used_colors = set()
        for nb in neighbors[idx]:
            if nb in colors:
                used_colors.add(colors[nb])

        # Assign lowest available color
        color = 0
        while color in used_colors:
            color += 1
        colors[idx] = color

    num_colors = max(colors.values()) + 1
    print(f"  Colored with {num_colors} layers")

    # Build result: color -> list of meshes
    result = defaultdict(list)
    for idx, color in colors.items():
        result[color].append(meshes[idx])
        short = meshes[idx].split("|")[-1]
        print(f"    [{short}] -> layer {color + 1}")

    return dict(result)


def main():
    all_meshes = []
    for t in cmds.ls(type="transform", long=True):
        shapes = cmds.listRelatives(t, shapes=True, type="mesh", fullPath=True)
        if shapes:
            all_meshes.append(t)

    if not all_meshes:
        print("No mesh objects found.")
        return

    print(f"Found {len(all_meshes)} mesh objects.")
    print(f"Padding: {PADDING} cm")

    bboxes = [get_world_bbox(m) for m in all_meshes]
    valid = [(m, b) for m, b in zip(all_meshes, bboxes) if b is not None]
    if not valid:
        print("Could not get bounding boxes.")
        return

    meshes = [m for m, _ in valid]
    bboxes = [b for _, b in valid]

    clusters = greedy_graph_coloring(meshes, bboxes, PADDING)

    # Delete old layers
    for old_layer in cmds.ls(type="displayLayer"):
        if old_layer.startswith("autoSeparate_"):
            try:
                cmds.delete(old_layer)
            except:
                pass

    # Create display layers
    for color in sorted(clusters.keys()):
        layer_name = f"autoSeparate_{color + 1:02d}"
        objs = clusters[color]
        print(f"\n  Creating {layer_name}: {len(objs)} objects")
        layer = cmds.createDisplayLayer(name=layer_name, empty=True)
        for obj in objs:
            try:
                cmds.editDisplayLayerMembers(layer, obj, noRecurse=True)
            except:
                pass

    print(f"\nDone! {len(clusters)} layers created.")
    print("Touching objects are guaranteed to be in different layers.")


if __name__ == "__main__":
    main()

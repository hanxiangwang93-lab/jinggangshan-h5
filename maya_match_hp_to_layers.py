"""
Maya - Match High-Poly to Existing Layers
==========================================
Run AFTER maya_cluster_by_distance.py.

For each unassigned mesh (e.g. high-poly), finds which
autoSeparate_* layer's objects it overlaps with most,
and adds it to that layer.
"""

import maya.cmds as cmds
from collections import defaultdict

# === Settings ===
LAYER_PREFIX = "autoSeparate_"  # prefix of layers to match against


def get_world_bbox(transform):
    try:
        return cmds.xform(transform, q=True, ws=True, boundingBox=True)
    except:
        return None


def bbox_overlap_volume(bb1, bb2):
    """Return the overlap volume of two bounding boxes (0 if no overlap)."""
    xmin1, ymin1, zmin1, xmax1, ymax1, zmax1 = bb1
    xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = bb2

    ox = min(xmax1, xmax2) - max(xmin1, xmin2)
    oy = min(ymax1, ymax2) - max(ymin1, ymin2)
    oz = min(zmax1, zmax2) - max(zmin1, zmin2)

    if ox <= 0 or oy <= 0 or oz <= 0:
        return 0.0
    return ox * oy * oz


def get_all_meshes():
    result = []
    for t in cmds.ls(type="transform", long=True):
        shapes = cmds.listRelatives(t, shapes=True, type="mesh", fullPath=True)
        if shapes:
            result.append(t)
    return result


def main():
    # Find existing autoSeparate_* layers
    layers = [l for l in cmds.ls(type="displayLayer") if l.startswith(LAYER_PREFIX)]
    if not layers:
        print(f"No layers found with prefix '{LAYER_PREFIX}'.")
        print("Run maya_cluster_by_distance.py first.")
        return

    layers.sort()
    print(f"Found {len(layers)} existing layers: {layers}")

    # Collect meshes already in these layers
    assigned = set()
    layer_bboxes = {}  # layer_name -> [list of bboxes]
    layer_mesh_names = defaultdict(list)

    for layer in layers:
        members = cmds.editDisplayLayerMembers(layer, q=True, fullNames=True) or []
        bboxes = []
        for m in members:
            assigned.add(m)
            bb = get_world_bbox(m)
            if bb:
                bboxes.append(bb)
            layer_mesh_names[layer].append(m.split("|")[-1])
        layer_bboxes[layer] = bboxes
        print(f"  {layer}: {len(members)} meshes -> {layer_mesh_names[layer][:5]}...")

    # Find unassigned meshes
    all_meshes = get_all_meshes()
    unassigned = [m for m in all_meshes if m not in assigned]
    if not unassigned:
        print("All meshes are already assigned to layers.")
        return

    print(f"\n{len(unassigned)} unassigned meshes to match...")

    # Match each unassigned mesh to best layer
    matched = 0
    for obj in unassigned:
        bb = get_world_bbox(obj)
        if not bb:
            continue

        best_layer = None
        best_score = -1.0

        for layer in layers:
            # Sum overlap volume with all meshes in this layer
            total_overlap = 0.0
            for lbb in layer_bboxes[layer]:
                total_overlap += bbox_overlap_volume(bb, lbb)

            if total_overlap > best_score:
                best_score = total_overlap
                best_layer = layer

        if best_layer and best_score > 0:
            cmds.editDisplayLayerMembers(best_layer, obj, noRecurse=True)
            print(f"  {obj.split('|')[-1]} -> {best_layer}  (overlap={best_score:.1f})")
            matched += 1
        elif best_layer:
            # No overlap with any layer - assign to closest
            print(f"  {obj.split('|')[-1]} -> {best_layer}  (no overlap, best guess)")

    if matched == 0:
        print("\nWARNING: No objects overlapped with existing layers.")
        print("Make sure LP and HP models are positioned together.")

    print(f"\nDone! {matched} objects assigned.")


if __name__ == "__main__":
    main()

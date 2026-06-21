"""
Maya - Export Bake Layers for Marmoset
=======================================
Run in Maya Script Editor (Python).

For each display layer, auto-detects LP/HP by polygon count:
  - Fewer faces  -> Low-Poly  (triangulated export)
  - More faces   -> High-Poly (no triangulation)

Also supports explicit naming: *_LP, *_HP suffixes override auto-detection.
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import re
from datetime import datetime

# === Set your project root (only once) ===
PROJECT_DIR = r'C:/Users/ASUS/Desktop/ksd'

_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
BASE = os.path.join(PROJECT_DIR, f'bake_export_{_timestamp}')
LOW_DIR = os.path.join(BASE, 'low')
HIGH_DIR = os.path.join(BASE, 'high')

os.makedirs(LOW_DIR, exist_ok=True)
os.makedirs(HIGH_DIR, exist_ok=True)

print(f"Exporting to: {BASE}")

LP_PAT = re.compile(r'(_LP|_low|_lo)$', re.IGNORECASE)
HP_PAT = re.compile(r'(_HP|_high|_hi)$', re.IGNORECASE)


def get_poly_count(obj):
    """Get triangle count of a mesh. Returns 0 for non-mesh objects."""
    try:
        return cmds.polyEvaluate(obj, triangle=True)
    except:
        return 0


def split_lp_hp(members):
    """
    Separate members into (lp_list, hp_list).
    Uses naming suffix first, then polygon-count gap detection.
    """
    lp = []
    hp = []
    unknown = []

    # Phase 1: naming suffix
    for obj in members:
        short = obj.split('|')[-1]
        if LP_PAT.search(short):
            lp.append(obj)
        elif HP_PAT.search(short):
            hp.append(obj)
        else:
            unknown.append(obj)

    # If naming handled everything, done
    if not unknown:
        return lp, hp

    # Phase 2: polygon-count gap detection for remaining objects
    if len(unknown) == 1:
        # Single unknown object among named ones -> classify by context
        # If we already have LP objects, this is probably HP, and vice versa
        if not lp and hp:
            lp = unknown
        elif not hp and lp:
            hp = unknown
        else:
            lp = unknown  # default to LP
        return lp, hp

    # Multiple unknown objects: split by largest poly-count gap
    mesh_info = [(obj, get_poly_count(obj)) for obj in unknown]
    mesh_info.sort(key=lambda x: x[1])

    if len(mesh_info) >= 2:
        # Find biggest ratio gap
        gaps = []
        for i in range(len(mesh_info) - 1):
            a = mesh_info[i][1]
            b = mesh_info[i + 1][1]
            ratio = b / max(a, 1)
            gaps.append((ratio, i))

        gaps.sort(reverse=True)
        _, split_idx = gaps[0]

        # Objects below gap -> LP, above gap -> HP
        for obj, count in mesh_info[:split_idx + 1]:
            lp.append(obj)
        for obj, count in mesh_info[split_idx + 1:]:
            hp.append(obj)

        ratio = gaps[0][0]
        if ratio < 2.0:
            print(f"    WARNING: LP/HP gap ratio only {ratio:.1f}x, check manually")
    else:
        lp = [obj for obj, _ in mesh_info]

    return lp, hp


# --- Main ---
all_layers = cmds.ls(type='displayLayer')
skip_layers = {'defaultLayer', 'defaultlayer'}
exported = 0

for layer in all_layers:
    if layer in skip_layers:
        continue

    members = cmds.editDisplayLayerMembers(layer, q=True, fullNames=True)
    if not members:
        continue

    # Filter to mesh objects only
    meshes = []
    for obj in members:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        for s in shapes:
            if cmds.nodeType(s) == 'mesh':
                meshes.append(obj)
                break

    if not meshes:
        print(f"  SKIP {layer}: no mesh objects")
        continue

    lp_objects, hp_objects = split_lp_hp(meshes)

    if not lp_objects:
        print(f"  SKIP {layer}: no low-poly objects detected")
        continue

    print(f"\nExporting: {layer}")
    print(f"  LP ({len(lp_objects)}): {[o.split('|')[-1] for o in lp_objects]}")
    if hp_objects:
        print(f"  HP ({len(hp_objects)}): {[o.split('|')[-1] for o in hp_objects]}")
    else:
        print(f"  HP: (none)")

    # --- Export Low-Poly (triangulated) ---
    cmds.select(lp_objects, replace=True)
    mel.eval('FBXExportTriangulate -v true')
    mel.eval('FBXExportSmoothingGroups -v false')
    mel.eval('FBXExportHardEdges -v false')

    lp_path = os.path.join(LOW_DIR, f'{layer}_LP.fbx')
    cmds.file(lp_path, force=True, options='v=0;', type='FBX export',
              pr=True, ea=True)
    print(f"  -> {os.path.basename(lp_path)} (triangulated)")

    # --- Export High-Poly (no triangulation) ---
    if hp_objects:
        cmds.select(hp_objects, replace=True)
        mel.eval('FBXExportTriangulate -v false')
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportHardEdges -v false')

        hp_path = os.path.join(HIGH_DIR, f'{layer}_HP.fbx')
        cmds.file(hp_path, force=True, options='v=0;', type='FBX export',
                  pr=True, ea=True)
        print(f"  -> {os.path.basename(hp_path)}")

    exported += 1

cmds.select(clear=True)

print(f"\nDone! {exported} layers exported to:")
print(f"  {LOW_DIR}")
print(f"  {HIGH_DIR}")
print(f"\nNext: place baking-quality HP FBX into:")
print(f"  {BASE}/high_bake/")

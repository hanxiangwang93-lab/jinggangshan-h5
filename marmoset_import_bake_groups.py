"""
Marmoset Toolbag 5 - Bake Group Auto-Setup
===========================================
Paste into TB5 Python Console, or adjust BASE path and run.

Generates one BakerObject with a group per Maya display layer.
Each group gets correct High/Low sub-container assignments.
"""

import mset
import os
import glob

# === Set your project root (only once) ===
PROJECT_DIR = r'C:/Users/ASUS/Desktop/ksd'

# Auto-find latest bake_export folder
_dirs = sorted(glob.glob(os.path.join(PROJECT_DIR, 'bake_export_*')), reverse=True)
if not _dirs:
    print(f"ERROR: No bake_export_* folder found under {PROJECT_DIR}")
    raise SystemExit()

BASE = _dirs[0]
print(f"Using: {BASE}")

LOW_DIR = BASE + '/low'
HIGH_DIR = BASE + '/high'

import os
if not os.path.isdir(LOW_DIR):
    print("ERROR: LOW_DIR not found. Update BASE path.")
else:
    low_files = sorted([f for f in os.listdir(LOW_DIR) if f.endswith('.fbx')])
    high_files = sorted([f for f in os.listdir(HIGH_DIR) if f.endswith('.fbx')]) if os.path.isdir(HIGH_DIR) else []

    mset.newScene()
    baker = mset.BakerObject()
    baker.name = 'MyBake'

    for lf in low_files:
        # Extract group name: "layer1_LP.fbx" -> "layer1"
        import re
        group_name = re.sub(r'(_LP|_low|_lo)\.fbx$', '', lf, flags=re.IGNORECASE)

        # Find matching high file
        matching_high = None
        for hf in high_files:
            hf_base = re.sub(r'(_HP|_high|_hi)\.fbx$', '', hf, flags=re.IGNORECASE)
            if hf_base == group_name:
                matching_high = hf
                break

        print(f"Setting up: {group_name}")

        g = baker.addGroup(group_name)
        lo = mset.importModel(LOW_DIR + '/' + lf)
        hi = mset.importModel(HIGH_DIR + '/' + matching_high) if matching_high else None

        gc = g.getChildren()
        gh = next(c for c in gc if c.name == 'High')
        gl = next(c for c in gc if c.name == 'Low')

        lo.parent = gl
        if hi is not None:
            hi.parent = gh

    print(f"Done! {len(low_files)} groups created in Baker panel.")

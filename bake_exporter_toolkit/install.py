"""
Bake Group Exporter - One-Click Installer
=========================================
Drop this file into Maya Script Editor (Python tab), Ctrl+Enter.
Auto-detects Maya version and user path. No manual config needed.

After install, type this in Maya Python tab each session to launch:
    import bakeGroupExporter; bakeGroupExporter.show()
"""

import os
import sys
import shutil
import maya.cmds as cmds

# ---- Auto-detect paths ----
MAYA_VERSION = str(cmds.about(version=True))
USER_DIR = os.path.expanduser("~")
SCRIPT_DEST = os.path.join(USER_DIR, "Documents", "maya", MAYA_VERSION, "scripts")
SRC_SCRIPT = os.path.join(os.path.dirname(__file__), "bakeGroupExporter.py")


def install():
    """Copy script to Maya scripts dir and add shelf button."""
    os.makedirs(SCRIPT_DEST, exist_ok=True)

    # 1. Copy main script
    if os.path.exists(SRC_SCRIPT):
        shutil.copy(SRC_SCRIPT, SCRIPT_DEST)
        print(f"[1/2] Script installed to: {SCRIPT_DEST}")
    else:
        print(f"[WARN] bakeGroupExporter.py not found next to this installer.")
        print(f"       Expected at: {SRC_SCRIPT}")
        return

    # 2. Add shelf button
    shelf_name = "Custom"
    if not cmds.shelfLayout(shelf_name, query=True, exists=True):
        cmds.shelfLayout(shelf_name, parent="ShelfLayout")

    cmds.setParent(shelf_name)
    cmds.shelfButton(
        label="BG",
        annotation="Bake Group Exporter",
        imageOverlayLabel="BG",
        image="render_into_texture.png",
        command="import bakeGroupExporter; bakeGroupExporter.show()",
        sourceType="python",
        width=35, height=35,
    )

    shelf_dir = cmds.internalVar(userShelfDir=True)
    os.makedirs(shelf_dir, exist_ok=True)
    try:
        cmds.saveAllShelves(shelf_dir)
    except RuntimeError:
        pass

    print(f"[2/2] Shelf button 'BG' added to '{shelf_name}' shelf.")
    print("")
    print("=== Installation Complete ===")
    print("Click the BG button on the Custom shelf to open the exporter.")
    print("Or run in Python tab: import bakeGroupExporter; bakeGroupExporter.show()")
    print("")
    print("Share this folder with others - they just run install.py once.")


if __name__ == "__main__":
    install()

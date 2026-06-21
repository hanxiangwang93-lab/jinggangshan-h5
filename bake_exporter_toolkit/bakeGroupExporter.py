"""
Maya Bake Group Exporter v1.0.0
Batch-export bake groups for Marmoset Toolbag.
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import json
import re
import time
from datetime import datetime

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance


VERSION = "1.0.0"
HIGH_SUFFIXES = ["_high", "_High", "_HIGH", "_hi", "_Hi"]
LOW_SUFFIXES = ["_low", "_Low", "_LOW", "_lo", "_Lo"]

MAYA_WINDOW_NAME = "bakeGroupExporterWindow"
MAYA_WINDOW_TITLE = f"Bake Group Exporter v{VERSION}"


# ============================================================================
# Detection (Display Layer based)
# ============================================================================

def get_mesh_vertex_count(mesh):
    """Return vertex count of a mesh. For transform nodes, checks first shape."""
    shapes = cmds.listRelatives(mesh, shapes=True, type="mesh", fullPath=True)
    if not shapes:
        return 0
    try:
        return cmds.polyEvaluate(shapes[0], vertex=True)
    except Exception:
        return 0


def get_all_meshes_in_scene():
    """Return all mesh transforms in the scene."""
    all_meshes = []
    for t in cmds.ls(type="transform", long=True):
        shapes = cmds.listRelatives(t, shapes=True, type="mesh", fullPath=True)
        if shapes:
            all_meshes.append(t)
    return all_meshes


def detect_bake_groups_by_layers():
    """
    Detect bake groups from Maya Display Layers.
    Each display layer = one bake group.
    Within each layer, pairs high/low by mesh name and vertex count.
    """
    layers = cmds.ls(type="displayLayer")
    # Filter out default layers
    skip_layers = {"defaultLayer", "DefaultLayer"}
    groups = []

    for layer in layers:
        if layer in skip_layers:
            continue

        # Get members of this layer
        members = cmds.editDisplayLayerMembers(layer, query=True, fullNames=True)
        if not members:
            continue

        # Filter to mesh transforms only
        mesh_members = []
        for m in members:
            shapes = cmds.listRelatives(m, shapes=True, type="mesh", fullPath=True)
            if shapes:
                mesh_members.append(m)

        if len(mesh_members) < 2:
            # A bake group needs at least low + one high
            continue

        # Separate high/low within this layer
        low_meshes, high_meshes = separate_high_low(mesh_members)

        if not low_meshes:
            # If we can't find a clear low-poly, use the lowest-vertex mesh as low
            sorted_by_vc = sorted(mesh_members, key=get_mesh_vertex_count)
            low_meshes = [sorted_by_vc[0]]
            high_meshes = sorted_by_vc[1:]

        groups.append({
            "name": layer,
            "high_grps": [],  # no transform groups; direct mesh list
            "low_grps": [],
            "high_meshes": high_meshes,
            "low_meshes": low_meshes,
        })

    return groups


def separate_high_low(mesh_list):
    """
    Given a list of mesh transforms, separate into high-poly and low-poly.
    Uses multiple strategies:
      1. Name suffix: *_high / *_low, *_HP / *_LP
      2. Name pattern: meshName vs meshName' (prime for high)
      3. Vertex count: fewer verts = low, more = high
    """
    low_meshes = []
    high_meshes = []

    # Strategy 1: Suffix matching
    remaining = []
    for m in mesh_list:
        short = m.split("|")[-1]
        if re.search(r'_(low|lo|lp|LOW|LO|LP)\b', short):
            low_meshes.append(m)
        elif re.search(r'_(high|hi|hp|HIGH|HI|HP)\b', short):
            high_meshes.append(m)
        else:
            remaining.append(m)

    # Strategy 2: Prime notation (A' = high, A = low)
    still_remaining = []
    for m in remaining:
        short = m.split("|")[-1]
        if short.endswith("'") or short.endswith("`"):
            high_meshes.append(m)
        else:
            still_remaining.append(m)

    # Strategy 3: Vertex count heuristic
    if still_remaining:
        # If no suffix-matched high/low at all, sort by vertex count and split
        if not low_meshes and not high_meshes:
            sorted_by_vc = sorted(still_remaining, key=get_mesh_vertex_count)
            # Lowest vertex count = low-poly
            low_meshes = [sorted_by_vc[0]]
            high_meshes = sorted_by_vc[1:]
        else:
            for m in still_remaining:
                vcount = get_mesh_vertex_count(m)
                if not high_meshes and low_meshes:
                    avg_low_vc = sum(get_mesh_vertex_count(x) for x in low_meshes) / len(low_meshes)
                    if vcount > avg_low_vc * 1.5:
                        high_meshes.append(m)
                        continue
                elif not low_meshes and high_meshes:
                    avg_high_vc = sum(get_mesh_vertex_count(x) for x in high_meshes) / len(high_meshes)
                    if vcount < avg_high_vc * 0.5:
                        low_meshes.append(m)
                        continue
                low_meshes.append(m)

    return low_meshes, high_meshes


def detect_bake_groups_by_hierarchy():
    """Fallback: detect via transform group hierarchy (original logic)."""
    def get_top_level_transforms():
        all_transforms = cmds.ls(type="transform", long=True)
        top = []
        for t in all_transforms:
            parent = cmds.listRelatives(t, parent=True, fullPath=True)
            if not parent:
                top.append(t)
        return top

    def has_mesh_children(transform):
        shapes = cmds.listRelatives(transform, allDescendents=True, type="mesh", fullPath=True)
        return shapes is not None and len(shapes) > 0

    top = get_top_level_transforms()
    groups = []
    for t in top:
        if not has_mesh_children(t):
            continue
        short = t.split("|")[-1]
        # Check for _high/_low pairs by base name
        base, suffix = None, None
        for s in HIGH_SUFFIXES + LOW_SUFFIXES:
            if short.endswith(s):
                base = short[:-len(s)]
                suffix = s
                break
        if base is None:
            continue

        # Find matching sibling groups
        siblings = [x for x in top if x != t and has_mesh_children(x)]
        pairs = {"high": [], "low": []}
        if suffix in HIGH_SUFFIXES:
            pairs["high"].append(t)
        else:
            pairs["low"].append(t)
        for sib in siblings:
            sib_short = sib.split("|")[-1]
            for s in HIGH_SUFFIXES:
                if sib_short == base + s:
                    pairs["high"].append(sib)
            for s in LOW_SUFFIXES:
                if sib_short == base + s:
                    pairs["low"].append(sib)

        if pairs["low"]:
            high_meshes = []
            for h in pairs["high"]:
                meshes = cmds.listRelatives(h, allDescendents=True, type="mesh", fullPath=True) or []
                high_meshes.extend(meshes)
            low_meshes = []
            for lo in pairs["low"]:
                meshes = cmds.listRelatives(lo, allDescendents=True, type="mesh", fullPath=True) or []
                low_meshes.extend(meshes)
            groups.append({
                "name": base,
                "high_grps": pairs["high"],
                "low_grps": pairs["low"],
                "high_meshes": high_meshes,
                "low_meshes": low_meshes,
            })
    return groups


def detect_all_bake_groups():
    """Detect bake groups: layers first, hierarchy as fallback."""
    layer_groups = detect_bake_groups_by_layers()

    if layer_groups:
        print(f"[Detection] Found {len(layer_groups)} group(s) from Display Layers")
        layer_groups.sort(key=lambda g: g["name"])
        return layer_groups

    # Fallback to hierarchy detection
    hier_groups = detect_bake_groups_by_hierarchy()
    print(f"[Detection] Found {len(hier_groups)} group(s) from hierarchy (no layers detected)")
    hier_groups.sort(key=lambda g: g["name"])
    return hier_groups


# ============================================================================
# FBX Export
# ============================================================================

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def export_group_fbx(group_data, output_dir, high_suffix="_HP", low_suffix="_LP"):
    group_name = sanitize_filename(group_data["name"])
    high_dir = os.path.join(output_dir, "high")
    low_dir = os.path.join(output_dir, "low")
    os.makedirs(high_dir, exist_ok=True)
    os.makedirs(low_dir, exist_ok=True)

    high_path = None
    low_path = None

    if group_data["high_meshes"]:
        cmds.select(group_data["high_meshes"], replace=True)
        high_path = os.path.join(high_dir, f"{group_name}{high_suffix}.fbx").replace("\\", "/")
        try:
            mel.eval(f'FBXExport -f "{high_path}" -s')
            print(f"  [OK] High: {high_path}")
        except Exception as e:
            print(f"  [FAIL] High: {e}")
            high_path = None

    if group_data["low_meshes"]:
        cmds.select(group_data["low_meshes"], replace=True)
        low_path = os.path.join(low_dir, f"{group_name}{low_suffix}.fbx").replace("\\", "/")
        try:
            mel.eval(f'FBXExport -f "{low_path}" -s')
            print(f"  [OK] Low: {low_path}")
        except Exception as e:
            print(f"  [FAIL] Low: {e}")
            low_path = None

    return high_path, low_path


# ============================================================================
# Marmoset Script Generator
# ============================================================================

def generate_marmoset_script(groups_data, output_dir, high_suffix="_HP", low_suffix="_LP"):
    """
    Generate a Python script for Marmoset Toolbag 5.
    One BakerObject with a group per Maya layer.
    Each group's High/Low sub-containers get the correct models.
    """
    low_dir = os.path.join(output_dir, "low").replace("\\", "/")
    high_dir = os.path.join(output_dir, "high").replace("\\", "/")

    lines = []
    lines.append("import mset")
    lines.append("")
    lines.append(f"BASE = r'{output_dir.replace(chr(92), '/')}'")
    lines.append("")
    lines.append("mset.newScene()")
    lines.append("")
    lines.append("baker = mset.BakerObject()")
    lines.append("baker.name = 'MyBake'")
    lines.append("")

    for g in groups_data:
        safe_name = sanitize_filename(g["name"])
        gname = g["name"]
        lines.append(f"# --- {gname} ---")
        lines.append(f"g = baker.addGroup('{gname}')")
        lines.append(f"lo = mset.importModel(BASE + '/low/{safe_name}{low_suffix}.fbx')")
        if g["high_meshes"]:
            lines.append(f"hi = mset.importModel(BASE + '/high/{safe_name}{high_suffix}.fbx')")
        else:
            lines.append("hi = None")
        lines.append("gc = g.getChildren()")
        lines.append("gh = next(c for c in gc if c.name == 'High')")
        lines.append("gl = next(c for c in gc if c.name == 'Low')")
        lines.append("lo.parent = gl")
        lines.append("if hi is not None:")
        lines.append("    hi.parent = gh")
        lines.append("")

    lines.append(f"print('Done! {len(groups_data)} groups in Baker panel.')")

    script_path = os.path.join(output_dir, "setup_bake_groups.py").replace("\\", "/")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] Marmoset 5 script: {script_path}")

    # Generate README
    readme_path = os.path.join(output_dir, "README.txt").replace("\\", "/")
    readme = "Bake Group Export for Marmoset Toolbag 5\n"
    readme += "=" * 50 + "\n\n"
    readme += "How to use:\n\n"
    readme += "  1. Open Marmoset Toolbag 5\n"
    readme += "  2. Scripts > Run Script... > choose 'setup_bake_groups.py'\n"
    readme += "  3. All FBX are imported, bake groups created automatically.\n\n"
    readme += "Bake Groups:\n"
    for g in groups_data:
        readme += f"  - {g['name']}: low={len(g['low_meshes'])} mesh(es), high={len(g['high_meshes'])} mesh(es)\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"  [OK] README: {readme_path}")
    return script_path


# ============================================================================
# UI
# ============================================================================

def get_maya_main_window():
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == "MayaWindow":
            return obj
    return None


def maya_ui_exists():
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == MAYA_WINDOW_NAME:
            return obj
    return None


class BakeGroupExporterUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(MAYA_WINDOW_NAME)
        self.setWindowTitle(MAYA_WINDOW_TITLE)
        self.setMinimumWidth(520)
        self.setMinimumHeight(500)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.groups = []
        self.build_ui()
        self.refresh_groups()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QtWidgets.QLabel("Bake Group Exporter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #eee; padding: 4px 0;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel(
            "Auto-detect bake groups from scene hierarchy, "
            "export FBX files, and generate Marmoset .marmoset_script."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(desc)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background: #444; max-height: 1px;")
        layout.addWidget(sep)

        layout.addWidget(QtWidgets.QLabel("Detected Bake Groups:"))
        self.group_list = QtWidgets.QListWidget()
        self.group_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2a; border: 1px solid #555; border-radius: 4px;
                color: #ddd; font-size: 12px;
            }
            QListWidget::item { padding: 6px 8px; border-bottom: 1px solid #3a3a3a; }
            QListWidget::item:selected { background: #3a5a8a; }
        """)
        self.group_list.setMinimumHeight(160)
        layout.addWidget(self.group_list)

        btn_row = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_groups)
        btn_row.addWidget(btn_refresh)

        btn_select = QtWidgets.QPushButton("Select in Viewport")
        btn_select.clicked.connect(self.select_in_viewport)
        btn_row.addWidget(btn_select)
        layout.addLayout(btn_row)

        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.HLine)
        sep2.setStyleSheet("background: #444; max-height: 1px;")
        layout.addWidget(sep2)

        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(QtWidgets.QLabel("Export To:"))
        self.path_edit = QtWidgets.QLineEdit()
        ws = cmds.workspace(query=True, rootDirectory=True) or os.path.expanduser("~")
        default_path = os.path.join(ws, "bake_exports")
        self.path_edit.setText(default_path)
        path_row.addWidget(self.path_edit)
        btn_browse = QtWidgets.QPushButton("...")
        btn_browse.setMaximumWidth(30)
        btn_browse.clicked.connect(self.browse_path)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        opts_grid = QtWidgets.QGridLayout()
        opts_grid.setSpacing(6)

        opts_grid.addWidget(QtWidgets.QLabel("Scene name:"), 0, 0)
        self.scene_name = QtWidgets.QLineEdit("BakeScene")
        opts_grid.addWidget(self.scene_name, 0, 1)

        opts_grid.addWidget(QtWidgets.QLabel("High suffix:"), 1, 0)
        self.high_suffix = QtWidgets.QLineEdit("_HP")
        self.high_suffix.setMaximumWidth(80)
        opts_grid.addWidget(self.high_suffix, 1, 1)

        opts_grid.addWidget(QtWidgets.QLabel("Low suffix:"), 2, 0)
        self.low_suffix = QtWidgets.QLineEdit("_LP")
        self.low_suffix.setMaximumWidth(80)
        opts_grid.addWidget(self.low_suffix, 2, 1)

        self.chk_marmoset_script = QtWidgets.QCheckBox("Generate setup script for Marmoset Toolbag 5")
        self.chk_marmoset_script.setChecked(True)
        opts_grid.addWidget(self.chk_marmoset_script, 3, 0, 1, 2)

        self.chk_open_folder = QtWidgets.QCheckBox("Open folder after export")
        self.chk_open_folder.setChecked(True)
        opts_grid.addWidget(self.chk_open_folder, 4, 0, 1, 2)

        layout.addLayout(opts_grid)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.log_label = QtWidgets.QLabel("")
        self.log_label.setStyleSheet("color: #888; font-size: 11px;")
        self.log_label.setWordWrap(True)
        layout.addWidget(self.log_label)

        self.btn_export = QtWidgets.QPushButton("Export All Bake Groups")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: #c05020; color: #fff; padding: 10px;
                font-size: 14px; font-weight: bold; border-radius: 4px;
                border: 1px solid #d06030;
            }
            QPushButton:hover { background: #d06030; }
            QPushButton:disabled { background: #444; color: #777; border-color: #555; }
        """)
        self.btn_export.clicked.connect(self.export_all)
        layout.addWidget(self.btn_export)

    def refresh_groups(self):
        self.group_list.clear()
        self.groups = detect_all_bake_groups()
        if not self.groups:
            self.group_list.addItem("  (No bake groups detected)")
            self.btn_export.setEnabled(False)
            return
        self.btn_export.setEnabled(True)
        for g in self.groups:
            hi_count = len(g["high_meshes"])
            lo_count = len(g["low_meshes"])
            item_text = f"{g['name']}  --  High: {hi_count} meshes  |  Low: {lo_count} meshes"
            self.group_list.addItem(item_text)
        self.log_label.setText(f"Detected {len(self.groups)} bake group(s).")

    def select_in_viewport(self):
        row = self.group_list.currentRow()
        if row < 0 or row >= len(self.groups):
            return
        g = self.groups[row]
        all_nodes = g["high_meshes"] + g["low_meshes"]
        cmds.select(all_nodes, replace=True)
        cmds.viewFit(all=True)

    def browse_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if path:
            self.path_edit.setText(path)

    def export_all(self):
        if not self.groups:
            QtWidgets.QMessageBox.warning(self, "No Groups", "No bake groups detected.")
            return

        output_dir = self.path_edit.text().strip()
        if not output_dir:
            QtWidgets.QMessageBox.warning(self, "No Path", "Please set an export directory.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(output_dir, f"bake_export_{ts}")
        os.makedirs(export_dir, exist_ok=True)

        scene_name = self.scene_name.text().strip() or "BakeScene"
        high_suffix = self.high_suffix.text().strip() or "_HP"
        low_suffix = self.low_suffix.text().strip() or "_LP"

        original_selection = cmds.ls(selection=True, long=True)

        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.groups))
        self.btn_export.setEnabled(False)

        success_count = 0
        exported = []

        for i, g in enumerate(self.groups):
            self.progress.setValue(i)
            self.log_label.setText(f"Exporting: {g['name']} ({i+1}/{len(self.groups)})...")
            QtWidgets.QApplication.processEvents()
            hi_path, lo_path = export_group_fbx(g, export_dir, high_suffix, low_suffix)
            if lo_path:
                exported.append(g)
                success_count += 1

        if self.chk_marmoset_script.isChecked() and exported:
            self.log_label.setText("Generating Marmoset 5 script...")
            QtWidgets.QApplication.processEvents()
            try:
                generate_marmoset_script(exported, export_dir, high_suffix, low_suffix)
            except Exception as e:
                print(f"[ERROR] Script generation failed: {e}")
                import traceback
                traceback.print_exc()

        if original_selection:
            cmds.select(original_selection, replace=True)

        self.progress.setValue(len(self.groups))
        self.log_label.setText(
            f"Exported {success_count}/{len(self.groups)} groups to:\n{export_dir}"
        )

        if self.chk_open_folder.isChecked():
            os.startfile(export_dir)

        self.btn_export.setEnabled(True)
        QtWidgets.QMessageBox.information(
            self, "Export Complete",
            f"Exported {success_count}/{len(self.groups)} bake groups.\n\n{export_dir}"
        )


def show():
    existing = maya_ui_exists()
    if existing:
        existing.close()
        existing.deleteLater()
    parent = get_maya_main_window()
    dialog = BakeGroupExporterUI(parent)
    dialog.show()
    return dialog


def export_all_headless(output_dir=None, scene_name="BakeScene",
                        high_suffix="_HP", low_suffix="_LP",
                        generate_scene=True):
    if output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ws = cmds.workspace(query=True, rootDirectory=True) or os.path.expanduser("~")
        output_dir = os.path.join(ws, "bake_exports", f"bake_export_{ts}")
    os.makedirs(output_dir, exist_ok=True)
    groups = detect_all_bake_groups()
    exported = []
    print(f"\n{'='*60}")
    print(f"Bake Group Exporter v{VERSION}")
    print(f"Found {len(groups)} group(s)")
    print(f"Exporting to: {output_dir}")
    print(f"{'='*60}\n")
    for g in groups:
        print(f"Group: {g['name']}")
        hi, lo = export_group_fbx(g, output_dir, high_suffix, low_suffix)
        if lo:
            exported.append(g)
    if generate_scene and exported:
        generate_marmoset_script(exported, output_dir, high_suffix, low_suffix)
    print(f"\nDone: {len(exported)}/{len(groups)} groups exported.")
    if generate_scene:
        print(f"Marmoset script: {os.path.join(output_dir, 'setup_bake_groups.py')}")
    return exported


if __name__ == "__main__":
    show()

import maya.cmds as cmds
import math

def flatten_faces():
    """
    将选中的多个面找平到它们的平均法线方向
    """
    selected_faces = cmds.ls(selection=True, flatten=True)
    if not selected_faces:
        cmds.warning("请先选择需要找平的面！")
        return

    for face in selected_faces:
        if '.f[' not in face:
            cmds.warning("请只选择面（Face）类型，而不是物体或边！")
            return

    normals = []
    for face in selected_faces:
        cmds.select(face)
        normal_info = cmds.polyInfo(face, faceNormals=True)
        if normal_info:
            parts = normal_info[0].split()
            if len(parts) >= 5:
                nx, ny, nz = float(parts[-3]), float(parts[-2]), float(parts[-1])
                normals.append((nx, ny, nz))

    if not normals:
        cmds.warning("无法获取所选面的法线信息！")
        return

    avg_nx = sum(n[0] for n in normals) / len(normals)
    avg_ny = sum(n[1] for n in normals) / len(normals)
    avg_nz = sum(n[2] for n in normals) / len(normals)

    length = math.sqrt(avg_nx**2 + avg_ny**2 + avg_nz**2)
    if length == 0:
        cmds.warning("法线向量为零，无法计算！")
        return
    avg_nx /= length
    avg_ny /= length
    avg_nz /= length

    all_vertices = []
    for face in selected_faces:
        verts = cmds.polyListComponentConversion(face, toVertex=True)
        verts = cmds.ls(verts, flatten=True)
        all_vertices.extend(verts)
    all_vertices = list(set(all_vertices))

    positions = []
    for vert in all_vertices:
        pos = cmds.pointPosition(vert, world=True)
        positions.append(pos)

    center_x = sum(p[0] for p in positions) / len(positions)
    center_y = sum(p[1] for p in positions) / len(positions)
    center_z = sum(p[2] for p in positions) / len(positions)

    cmds.select(selected_faces)
    cmds.polySelectConstraint(mode=3, type=8, orient=2,
        orientaxis=(avg_nx, avg_ny, avg_nz),
        orientbound=(0, 180))

    for vert in all_vertices:
        pos = cmds.pointPosition(vert, world=True)
        dx = pos[0] - center_x
        dy = pos[1] - center_y
        dz = pos[2] - center_z
        dist = dx * avg_nx + dy * avg_ny + dz * avg_nz
        new_x = pos[0] - dist * avg_nx
        new_y = pos[1] - dist * avg_ny
        new_z = pos[2] - dist * avg_nz
        cmds.move(new_x, new_y, new_z, vert, absolute=True)

    cmds.polySelectConstraint(dis=True)
    print("找平操作完成！共处理 {} 个面的 {} 个顶点".format(len(selected_faces), len(all_vertices)))

flatten_faces()

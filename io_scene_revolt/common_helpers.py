import bpy
import bmesh
from mathutils import Vector, Matrix

import os
import os.path as path

# constants
RV_LEVEL_SCALE = 10.0

POLY_FLAG_QUAD = 0x01
POLY_FLAG_DOUBLESIDED = 0x02
POLY_FLAG_TRANSLUCENT = 0x04
POLY_FLAG_DISABLEENV = 0x400
POLY_FLAG_ENABLEENV = 0x800


def prepare_bmesh(bm, max_sides=4):
    tria_faces = [face for face in bm.faces if len(face.loops) > max_sides]
    if len(tria_faces) > 0:
        bmesh.ops.triangulate(bm, faces=tria_faces, quad_method='BEAUTY', ngon_method='BEAUTY')


def bounds(obj, local=False):
    local_coords = obj.bound_box[:]

    if not local:    
        om = obj.matrix_world
        worldify = lambda p: (om @ Vector(p[:]))
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)


def bounds_scaled(obj, scale, local=False):
    bounds_unscaled = bounds(obj, local)
    for x in range(3):
        bounds_unscaled[x].min *= scale
        bounds_unscaled[x].max *= scale
    return bounds_unscaled


def vec3_to_revolt(co):
    return (co[0], co[2] * -1, co[1])


def vec2_to_revolt(co):
    return (co[0], 1 - co[1])

 
def to_rv_color(color):
    r = int(max(0, min(color[0], 1)) * 255)
    g = int(max(0, min(color[1], 1)) * 255)
    b = int(max(0, min(color[2], 1)) * 255)
    a = int(max(0, min(color[3], 1)) * 255)
    return (b,g,r,a)


def get_material_texture(mat):
    tree = mat.node_tree.nodes if mat.node_tree is not None else []    
    for node in tree:
        if node.type == 'TEX_IMAGE':
            return node.image
    return None


def get_texnum_from_texname(texname):
    return_num = -1
    last_char = texname[-1]
    if last_char >= 'a' and last_char <= 'z':
        return_num = ord(last_char) - ord('a')
    elif last_char >= 'A' and last_char <= 'Z':
        return_num = ord(last_char) - ord('A')
    return return_num
    
def get_texnum_from_material(material):
    if material is None:
        return -1
        
    texture = get_material_texture(material)
    if texture is None or texture.filepath == "": # default
        return -1
        
    file_path = texture.filepath
    file_name = os.path.basename(file_path)
    file_path_noext = os.path.splitext(file_name)[0]
    
    texnum = get_texnum_from_texname(file_path_noext)
    return texnum
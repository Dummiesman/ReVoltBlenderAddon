import bpy
import bmesh
from mathutils import Vector, Matrix

import os
import os.path as path

# constants
RV_LEVEL_SCALE = 10.0
RV_MESH_SCALE = 10.0

POLY_FLAG_QUAD = 0x01
POLY_FLAG_DOUBLESIDED = 0x02
POLY_FLAG_TRANSLUCENT = 0x04
POLY_FLAG_DISABLEENV = 0x400
POLY_FLAG_ENABLEENV = 0x800

COLL_FLAG_QUAD = 0x01
COLL_FLAG_OBJECT_ONLY = 0x04
COLL_FLAG_CAMERA_ONLY = 0x08

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

    bnds_min = [float('inf'),float('inf'),float('inf')]
    bnds_max = [float('-inf'),float('-inf'),float('-inf')]
    
    for (axis, _list) in zip((0,1,2), rotated):
        bnds_min[axis] = min(bnds_min[axis], min(_list))
        bnds_max[axis] = max(bnds_max[axis], max(_list))

    return (bnds_min, bnds_max)


def bounds_scaled(obj, scale, local=False):
    bnds_min, bnds_max = bounds(obj, local)
    for x in range(3):
        bnds_min[x] *= scale
        bnds_max[x] *= scale
    return (bnds_min, bnds_max)
    
    
def bounds_rv(obj, local=False):
    bnds_min, bnds_max = bounds(obj, local)
    bnds_min = vec3_to_revolt(bnds_min)
    bnds_max = vec3_to_revolt(bnds_max)
    return ((bnds_min[0], bnds_max[1], bnds_min[2]), (bnds_max[0], bnds_min[1], bnds_max[2]))


def bounds_scaled_rv(obj, scale, local=False):
    bnds_min, bnds_max = bounds_scaled(obj, scale, local)
    bnds_min = vec3_to_revolt(bnds_min)
    bnds_max = vec3_to_revolt(bnds_max)
    return ((bnds_min[0], bnds_max[1], bnds_min[2]), (bnds_max[0], bnds_min[1], bnds_max[2]))

    
def face_bounds(face):
    bnds_min = [float('inf'),float('inf'),float('inf')]
    bnds_max = [float('-inf'),float('-inf'),float('-inf')]
    for vert in face.verts:
        for x in range(3):
            bnds_min[x] = min(bnds_min[x], vert.co[x])
            bnds_max[x] = max(bnds_max[x], vert.co[x])
                
    return (bnds_min, bnds_max)


def face_bounds_rv(face):
    bnds_min, bnds_max = face_bounds(face)
    bnds_min = vec3_to_revolt(bnds_min)
    bnds_max = vec3_to_revolt(bnds_max)
    return ((bnds_min[0], bnds_max[1], bnds_min[2]), (bnds_max[0], bnds_min[1], bnds_max[2]))


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


def get_material_from_material_slot(ob, slotnum):
    if len(ob.material_slots) == 0 or slotnum < 0:
        return None
        
    slot = ob.material_slots[slotnum]
    return slot.material
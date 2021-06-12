import bpy
import bmesh
from mathutils import Vector, Matrix

import os
import os.path as path

# constants
POLY_FLAG_QUAD = 0x01
POLY_FLAG_DOUBLESIDED = 0x02
POLY_FLAG_TRANSLUCENT = 0x04
POLY_FLAG_MIRROR = 0x80
POLY_FLAG_ADDITIVE = 0x100
POLY_FLAG_DISABLEENV = 0x400
POLY_FLAG_ENABLEENV = 0x800

COLL_FLAG_QUAD = 0x01
COLL_FLAG_OBJECT_ONLY = 0x04
COLL_FLAG_CAMERA_ONLY = 0x08

RV_SCALE = 10
BCUBE_SIZE = 12500

def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name


def find_objects_by_name(name, ob_type = 'MESH'):
    objs = []
    for ob in bpy.data.objects:
        if ob.type == ob_type:
            undupe_name = get_undupe_name(ob.name)
            if undupe_name.lower() == name.lower():
                objs.append(ob)
                
    return objs  


def create_colored_material(name, color):
    color_list = [1, 1, 1, 1]
    for x in range(min(len(color_list), len(color))):
        color_list[x] = color[x]
    
    mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    mat.use_backface_culling = True
    
    nodetree = mat.node_tree
    nodetree.links.clear()
    nodetree.nodes.clear()
        
    diffuse = nodetree.nodes.new(type = 'ShaderNodeBsdfDiffuse')
    output = nodetree.nodes.new(type = 'ShaderNodeOutputMaterial' )
    
    nodetree.links.new( diffuse.outputs['BSDF'], output.inputs['Surface'] )
    
    diffuse.inputs['Color'].default_value = color_list
    mat.diffuse_color = color_list
    
    return mat


def vec3_to_revolt(co):
    return (co[0], co[2] * -1, co[1])


def vec2_to_revolt(co):
    return (co[0], 1 - co[1])


def vec3_to_blender(co):
    return (co[0], co[2], co[1] * -1)
    
    
def vec2_to_blender(co):
    # symmetric operation
    return vec2_to_revolt(co)


def from_rv_color(color):
    b = max(0, min(float(color[0]) / 255, 1))
    g = max(0, min(float(color[1]) / 255, 1))
    r = max(0, min(float(color[2]) / 255, 1))
    a = max(0, min(float(color[3]) / 255, 1))
    return (r,g,b,a)


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


def bmesh_bounds(bm):
    bnds_min = [float('inf'),float('inf'),float('inf')]
    bnds_max = [float('-inf'),float('-inf'),float('-inf')]
    for vert in bm.verts:
        for x in range(3):
            bnds_min[x] = min(bnds_min[x], vert.co[x])
            bnds_max[x] = max(bnds_max[x], vert.co[x])

    return (bnds_min, bnds_max)
    
    
def bmesh_bounds_scaled(bm, scale):
    bnds_min, bnds_max = bmesh_bounds(bm)
    for x in range(3):
        bnds_min[x] *= scale
        bnds_max[x] *= scale
    
    return (bnds_min, bnds_max)


def bmesh_bounds_rv(bm):
    bnds_min, bnds_max = bmesh_bounds(bm)
    bnds_min = vec3_to_revolt(bnds_min)
    bnds_max = vec3_to_revolt(bnds_max)
    return ((bnds_min[0], bnds_max[1], bnds_min[2]), (bnds_max[0], bnds_min[1], bnds_max[2]))


def bmesh_bounds_scaled_rv(bm, scale):
    bnds_min, bnds_max = bmesh_bounds_scaled(bm, scale)
    bnds_min = vec3_to_revolt(bnds_min)
    bnds_max = vec3_to_revolt(bnds_max)
    return ((bnds_min[0], bnds_max[1], bnds_min[2]), (bnds_max[0], bnds_min[1], bnds_max[2]))


def bm_to_world(bm, ob):
    for vert in bm.verts:
        vert.co = ob.matrix_world @ vert.co


def get_principled_from_material(mat):
    tree = mat.node_tree.nodes if mat.node_tree is not None else []    
    for node in tree:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def set_material_vertex_blend(mat):
    if mat is None or mat.node_tree is None:
        return

    principled_data = get_principled_from_material(mat)
    if principled_data is None:
        return
    
    color_input = principled_data.inputs['Base Color']
    old_input = None
    vc_output = None
    
    if len(color_input.links) > 0:
        link = color_input.links[0]
        old_input = link.from_socket
        mat.node_tree.links.remove(link)
    else:
        vc_output = color_input
        
    # create node setup
    if old_input is not None:
        vec_math_node = mat.node_tree.nodes.new('ShaderNodeVectorMath')
        vec_math_node.operation = 'MULTIPLY'
        vc_output = vec_math_node.inputs[0]
        
        mat.node_tree.links.new(old_input, vec_math_node.inputs[1])
        mat.node_tree.links.new(vec_math_node.outputs[0], color_input)
        
        
    vert_color_node = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    mat.node_tree.links.new(vert_color_node.outputs['Color'], vc_output)
    
    
def set_material_texture(mat, texture, make_image_node=True):
    if mat is None or mat.node_tree is None:
        return
    
    tree = mat.node_tree.nodes
    for node in tree:
        if node.type == 'TEX_IMAGE':
            node.image = texture
            return
            
    # image node was not found
    if make_image_node:
        principled_data = get_principled_from_material(mat)
        if principled_data is not None:
            color_input = principled_data.inputs['Base Color']
            
            # something is already here?
            if len(color_input.links) > 0:
                return
                
            # create and hook up our image
            tex_image_node = tree.new('ShaderNodeTexImage')
            tex_image_node.image = texture
            
            mat.node_tree.links.new(principled_data.inputs['Base Color'], tex_image_node.outputs['Color'])
    

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
    
######################################################
# LOAD PREFS
######################################################
preferences = bpy.context.preferences
addon_prefs = preferences.addons[__package__].preferences
RV_SCALE = addon_prefs.scale

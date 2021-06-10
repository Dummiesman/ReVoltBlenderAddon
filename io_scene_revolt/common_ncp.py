import bpy

FACEMAP_OBJECT_ONLY = "Object Only"
FACEMAP_CAMERA_ONLY = "Camera Only"

# Materials are ID, Name, Color
# names and colors from Huki's Re-Volt Addon For Blender
# https://gitlab.com/re-volt/re-volt-addon/-/blob/master/io_revolt/common.py#L156
NCP_MATERIALS = [(0, "DEFAULT",              (0.6,0.6,0.6)),
                 (1, "MARBLE",               (0.51,0.36,0.36)),
                 (2, "STONE",                (0.22,0.22,0.22)),
                 (3, "WOOD",                 (0.47,0.3,0.14)),
                 (4, "SAND",                 (0.96,0.76,0.5)),
                 (5, "PLASTIC",              (0.09,0.09,0.09)),
                 (6, "CARPETTILE",           (0.67,0.08,0)),
                 (7, "CARPETSHAG",           (0.53,0.18,0.13)),
                 (8, "BOUNDARY",             (1,0,1)),
                 (9, "GLASS",                (1,1,1)),
                 (10, "ICE1",                (0.72,1,0.95)),
                 (11, "METAL",               (0.53,0.6,0.64)),
                 (12, "GRASS",               (0.18,0.36,0.05)),
                 (13, "BUMPMETAL",           (0.22,0.24,0.2)),
                 (14, "PEBBLES",             (0.55,0.55,0.49)),
                 (15, "GRAVEL",              (0.79,0.77,0.76)),
                 (16, "CONVEYOR1",           (0.22,0,0.5)),
                 (17, "CONVEYOR2",           (0.2,0.15,0.24)),
                 (18, "DIRT1",               (0.53,0.39,0.29)),
                 (19, "DIRT2",               (0.36,0.26,0.19)),
                 (20, "DIRT3",               (0.26,0.16,0.1)),
                 (21, "ICE2",                (0.52,0.71,0.7)),
                 (22, "ICE3",                (0.4,0.53,0.53)),
                 (23, "WOOD2",               (0.47,0.3,0.17)),
                 (24, "CONVEYOR_MARKET1",    (0,0.08,0.22)),
                 (25, "CONVEYOR_MARKET2",    (0.1,0.13,0.2)),
                 (26, "PAVING",              (0.56,0.5,0.45))]


def create_colored_material(name, color):
    mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    mat.use_backface_culling = True
    
    nodetree = mat.node_tree
    nodetree.links.clear()
    nodetree.nodes.clear()
        
    diffuse = nodetree.nodes.new(type = 'ShaderNodeBsdfDiffuse')
    output = nodetree.nodes.new(type = 'ShaderNodeOutputMaterial' )
    
    nodetree.links.new( diffuse.outputs['BSDF'], output.inputs['Surface'] )
    
    diffuse.inputs['Color'].default_value = (*color, 1)
    mat.diffuse_color = (*color,1)
    
    return mat

 
def get_ncp_id_from_material(mat):
    if mat is not None:
        if "ncp_material_id" in mat:
            ncp_id = mat["ncp_material_id"]
            if isinstance(ncp_id, (int, float)):
                return int(ncp_id)
    return None

        
def find_ncp_material(material_id):
    for mat in bpy.data.materials:
        if get_ncp_id_from_material(mat) == material_id:
            return mat
    return None

def create_shared_ncp_materials():
    for m_id, m_name, m_color in NCP_MATERIALS:
        existing = find_ncp_material(m_id)
        if existing is None:
            newmat = create_colored_material("NCP_" + m_name, m_color)
            newmat["ncp_material_id"] = m_id

def add_ncp_materials(ob):
    # make sure they exist
    create_shared_ncp_materials()
    
    # add missing ones
    exclude_add = {}
    for slot in ob.material_slots:
        if slot.material is not None:
            if "ncp_material_id" in slot.material:
                exclude_add[slot.material["ncp_material_id"]] = True
                
    for m_info in NCP_MATERIALS:
        m_id = m_info[0]
        if not m_id in exclude_add:
            mat_to_add = find_ncp_material(m_id)
            ob.data.materials.append(mat_to_add)
    
    
def add_ncp_facemaps(ob):
    if not FACEMAP_OBJECT_ONLY in ob.face_maps:
        ob.face_maps.new( name = FACEMAP_OBJECT_ONLY )
    if not FACEMAP_CAMERA_ONLY in ob.face_maps:
        ob.face_maps.new( name = FACEMAP_CAMERA_ONLY )
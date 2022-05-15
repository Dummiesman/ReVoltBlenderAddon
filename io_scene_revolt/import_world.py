import bpy
import bmesh
import struct, math, time, collections, os
from mathutils import Vector

import io_scene_revolt.common_helpers as common
from io_scene_revolt.rvfacehash import RV_FaceMaterialHash

######################################################
# HELPERS
######################################################
def read_texanims_from_w(file):
    scene = bpy.context.scene
    animtex = scene.rv_animtex
    anims = animtex.slots
    
    # clear existing
    animtex.clear()
    
    #
    anim_count = struct.unpack("<L", file.read(4))[0]
    for x in range(anim_count):
        anim = anims.add()
        frame_count = struct.unpack("<L", file.read(4))[0]
        
        for y in range(frame_count):
            frame = anim.frames.add()
            
            frame_tex, frame_delay = struct.unpack("<lf", file.read(8))
            uv0 = struct.unpack("<ff", file.read(8))
            uv1 = struct.unpack("<ff", file.read(8))
            uv2 = struct.unpack("<ff", file.read(8))
            uv3 = struct.unpack("<ff", file.read(8))
            
            frame.texture_number = frame_tex
            frame.delay = frame_delay
            frame.set_uv(0, uv0)
            frame.set_uv(1, uv1)
            frame.set_uv(2, uv2)
            frame.set_uv(3, uv3)
    

def seek_past_mesh(file, psx = False):
    poly_size = 36 if psx else 60
    vert_size = 12 if psx else 24
    
    # seek past bounding info
    file.seek(8 if psx else 40, 1)
    
    poly_count, vertex_count = struct.unpack("<HH", file.read(4))
    
    # seek past polygons and verts
    if psx:
        file.seek(poly_count * poly_size, 1)
    else:
        file.seek((poly_count * poly_size) + (vertex_count * vert_size), 1)

    
def seek_past_bcubes(file, psx = False):
    bcube_count = 0
    if psx:
        bcube_count = struct.unpack("<H", file.read(2))[0]
    else:
        bcube_count = struct.unpack("<L", file.read(4))[0]
    
    for x in range(bcube_count):
        # seek past center/radius
        file.seek(8 if psx else 16, 1)
        
        if psx:
            index_count = struct.unpack("<H", file.read(2))[0]
            file.seek(index_count * 2, 1)
        else:
            index_count = struct.unpack("<L", file.read(4))[0]
            file.seek(index_count * 4, 1)

    
def finalize_world_materials(filepath, materials):
    filepath_noext = os.path.splitext(filepath)[0]
    loaded_textures = {}
    
    for mat in materials:
        if "NoTex" in mat.name or not "RVMaterial" or "Anim" in mat.name:
            continue
        
        # extract texnum from material name
        name = common.get_undupe_name(mat.name)
        texnum = 0        

        tex_index = common.str_index_safe(name, "Tex")
        if tex_index < 0:
            continue
            
        uscore_index = common.str_index_safe(name, "_", tex_index)
        if uscore_index >= 0:
            texnum = int(name[tex_index+3:uscore_index])
        else:
            texnum = int(name[tex_index+3:])
    
        # load or set texture
        if texnum in loaded_textures:
            texture = loaded_textures[texnum]
            if texture is not None:
                common.set_material_texture(mat, loaded_textures[texnum])
        else:
            texchar = chr(texnum + ord('a'))
            texpath = filepath_noext + texchar + ".bmp"
            
            if os.path.isfile(texpath):
                loaded_textures[texnum] = bpy.data.images.load(texpath)
                common.set_material_texture(mat, loaded_textures[texnum])
            else:
                loaded_textures[texnum] = None

    for mat in materials:
        common.set_material_vertex_blend(mat)

######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath=""
         ):
    
    import io_scene_revolt.import_mesh as import_mesh
    print("importing World: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # import world
    file = open(filepath, 'rb')
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0, 0)
    
    is_psx = filepath.lower().endswith(".psw")

    env_list = collections.deque()
    vert_list = [] if is_psx else None

    # seek alllllll the way to the end to get our env list on PC
    # otherwise we seek to the end for vert list for PSX
    mesh_count = struct.unpack("<L", file.read(4))[0]
    meshes_file_pos = file.tell()    

    for x in range(mesh_count):
        seek_past_mesh(file, psx = is_psx)
            
    seek_past_bcubes(file, psx = is_psx)
        
    # read texanims, and env list if pc
    # else read vertices if psx
    if not is_psx:
        # some files just end here
        if file.tell() < file_size:
            # read texanims 
            read_texanims_from_w(file)

            # we're here
            env_list_file_pos = file.tell()
            file.seek(0, 2)
            env_list_length = file.tell() - env_list_file_pos
            env_list_count = int(env_list_length / 4)
            file.seek(env_list_file_pos)
            
            for x in range(env_list_count):
                color = struct.unpack("<BBBB", file.read(4))
                color = common.from_rv_color(color)
                env_list.append(color)

    else:
        # read vertices
        vertex_count = struct.unpack("<L", file.read(4))[0]
        for x in range(vertex_count):
            vert = Vector(struct.unpack("<hhh", file.read(6))) / common.RV_SCALE
            normal = struct.unpack("<hhh", file.read(6))
            
            vert_list.append(common.vec3_to_blender(vert))
            
            
    # now go back and read meshes
    file.seek(meshes_file_pos)
    
    # load_mesh(file, is_world, env_queue, matdict = None):
    shared_matdict = {}
    for x in range(mesh_count):
        import_mesh.load_mesh(file, is_world = True, env_queue = env_list, matdict = shared_matdict, psx = is_psx, vertlist = vert_list)
    
    # cleanup     
    file.close()
    
    # load textures
    unique_materials = set(shared_matdict.values())
    finalize_world_materials(filepath, unique_materials)
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
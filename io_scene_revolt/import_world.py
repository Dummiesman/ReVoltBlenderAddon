import bpy
import bmesh
import struct, math, time, collections
from mathutils import Vector

import io_scene_revolt.common_helpers as common
from io_scene_revolt.rvfacehash import RV_FaceMaterialHash

######################################################
# HELPERS
######################################################
def seek_past_mesh(file):
    poly_size = 60
    vert_size = 24
    
    # seek past bounding info
    file.seek(40, 1)
    
    poly_count, vertex_count = struct.unpack("<HH", file.read(4))
    # seek past polygons and verts
    file.seek((poly_count * poly_size) + (vertex_count * vert_size), 1)

    
def seek_past_fball(file):
    # seek past center/radius
    file.seek(16, 1)
    
    index_count = struct.unpack("<L", file.read(4))[0]
    file.seek(index_count * 4, 1)

    
def seek_past_texanim(file):
    frame_count = struct.unpack("<L", file.read(4))[0]
    file.seek(40 * frame_count, 1)
        

def load_world_textures(filepath, materials):
    # todo :)
    pass

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
    
    # seek alllllll the way to the end to get our env list.
    mesh_count = struct.unpack("<L", file.read(4))[0]
    meshes_file_pos = file.tell()
    for x in range(mesh_count):
        seek_past_mesh(file)
        
    fball_count = struct.unpack("<L", file.read(4))[0]
    for x in range(fball_count):
        seek_past_fball(file)
        
    anim_count = struct.unpack("<L", file.read(4))[0]
    for x in range(anim_count):
        seek_past_texanim(file)

    # we're here
    env_list_file_pos = file.tell()
    file.seek(0, 2)
    env_list_length = file.tell() - env_list_file_pos
    env_list_count = int(env_list_length / 4)
    file.seek(env_list_file_pos)
    
    env_list = collections.deque()
    for x in range(env_list_count):
        color = struct.unpack("<BBBB", file.read(4))
        color = common.from_rv_color(color)
        env_list.append(color)
    
    # now go back and read meshes
    file.seek(meshes_file_pos)
    
    # load_mesh(file, is_world, env_queue, matdict = None):
    shared_matdict = {}
    for x in range(mesh_count):
        import_mesh.load_mesh(file, True, env_list, shared_matdict)
    
    # cleanup     
    file.close()
    
    # load textures
    unique_materials = set()
    for k in shared_matdict:
        mat = shared_matdict[k]
        unique_materials.add(mat.name)
    load_world_textures(filepath, unique_materials)
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
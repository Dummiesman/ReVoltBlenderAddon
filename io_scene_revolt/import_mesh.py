import bpy, bmesh
import struct, math, time, collections, os
from mathutils import Vector

import io_scene_revolt.common_helpers as common
from io_scene_revolt.rvfacehash import RV_FaceMaterialHash

######################################################
# HELPERS
######################################################
def finalize_mesh_materials_stage1(filepath, materials):
    filepath_lower = filepath.lower()
    look_for_texture = None
    
    if filepath_lower.endswith("body.psm"):
        look_for_texture = "TEXTURE.bmp"
    elif filepath_lower.endswith("zody.psm"):
        look_for_texture = "ZEXTURE.bmp"
    elif filepath_lower.endswith("body.prm"):
        look_for_texture = "car.bmp"
    
    if look_for_texture is None:
        return

    filepath_dir = os.path.dirname(filepath)
    carbmp_path = os.path.join(filepath_dir, look_for_texture)
    
    if not os.path.isfile(carbmp_path):
        return
    
    carbmp = bpy.data.images.load(carbmp_path)
    for mat in materials:
        if "NoTex" in mat.name or not "RVMaterial" in mat.name:
            continue
        common.set_material_texture(mat, carbmp)
        

def finalize_mesh_materials_stage2(filepath, materials):
    for mat in materials:
        common.set_material_vertex_blend(mat)

######################################################
# IMPORT
######################################################
def load_mesh(file, is_world = False, env_queue = None, matdict = None, psx = False, vertlist = None):
    poly_size = 36 if psx else 60
    
    # create the object
    scn = bpy.context.scene
    
    me = bpy.data.meshes.new("Mesh")
    ob = bpy.data.objects.new("Mesh", me)
    bm = bmesh.new()
    scn.collection.objects.link(ob)
    
    # create layers for this object
    uv_layer = bm.loops.layers.uv.new()
    vc_layer = bm.loops.layers.color.new()
    
    # seek past bounding info if world
    if is_world:
        file.seek(8 if psx else 40, 1)
    
    # read mesh
    face_hashes = []
    face_materials = {} if matdict is None else matdict
    face_materials_to_matslot = {}
    
    vert_remap = {} 
    used_verts = []

    poly_count, vertex_count = struct.unpack("<HH", file.read(4))
    poly_file_location = file.tell() 
    file.seek(poly_size * poly_count, 1)
    
    # read in vertices
    if vertlist is None:
        vertlist = []
        if psx:
            for x in range(vertex_count):
                vert = Vector(struct.unpack("<hhh", file.read(6))) / common.RV_SCALE / common.PSX_VERTEX_DIVISOR
                vert = common.vec3_to_blender(vert)
                
                normal = Vector(struct.unpack("<hhh", file.read(6))) / common.PSX_NORMAL_DIVISOR
                normal = common.vec3_to_blender(normal)
                
                vertlist.append(vert)
        else:
            for x in range(vertex_count):
                vert = Vector(struct.unpack("<fff", file.read(12))) / common.RV_SCALE
                vert = common.vec3_to_blender(vert)
                
                normal = struct.unpack("<fff", file.read(12))
                normal = common.vec3_to_blender(normal)
                
                vertlist.append(vert)
        
    bm.verts.ensure_lookup_table()
    mesh_end_file_location = file.tell()    
    
    # read in polygons
    file.seek(poly_file_location)
    for x in range(poly_count):
        poly_type, poly_texture = struct.unpack("<Hh", file.read(4))
        vertex_indices = list(struct.unpack("<HHHH", file.read(8)))
        loop_count = 4 if poly_type & common.POLY_FLAG_QUAD else 3
        
        vertex_colors = []
        uvs = []
        
        # remap (not typically needed, but PSW has a global vertex list, so we do this)
        for x in range(loop_count):
            index = vertex_indices[x]
            new_index = -1
            if not index in vert_remap:
                new_index = len(used_verts)
                vert_remap[index] = new_index
                
                vert = vertlist[index]
                bmvert = bm.verts.new(vert)
                used_verts.append(bmvert)
            else:
                new_index = vert_remap[index]

            vertex_indices[x] = new_index
            
        # colors
        for y in range(4):
            color = struct.unpack("<BBBB", file.read(4))
            color = common.from_rv_color_psx(color) if psx else common.from_rv_color(color)
            vertex_colors.append(color)

        # uvs
        if psx:
            for y in range(4):
                uv = list(struct.unpack("<BB", file.read(2)))
                uv[0] /= 255.0
                uv[1] /= 255.0
                uvs.append(common.vec2_to_blender(uv))
        else:
            for y in range(4):
                uv = struct.unpack("<ff", file.read(8))
                uvs.append(common.vec2_to_blender(uv))
           
        # hash, and get material
        poly_hash = RV_FaceMaterialHash(poly_texture, poly_type, is_world)
        if is_world and poly_type & common.POLY_FLAG_ENABLEENV and env_queue is not None and len(env_queue) > 0:
            poly_hash.set_env_color(env_queue.popleft())
          
        if poly_type & common.POLY_FLAG_TRANSLUCENT:
            avg_alpha = 0
            for y in range(loop_count):
                avg_alpha += vertex_colors[y][3]
            avg_alpha /= loop_count
            poly_hash.set_alpha(avg_alpha)
            
        face_hashes.append(poly_hash)    
        
        mat = None
        if not poly_hash in face_materials:
            mat = poly_hash.make_material()
            face_materials[poly_hash] = mat
        else:
            mat = face_materials[poly_hash]
        
        mat_index = -1
        if not poly_hash in face_materials_to_matslot:
            mat_index = len(ob.material_slots)
            ob.data.materials.append(mat)
            face_materials_to_matslot[poly_hash] = mat_index
        else:
            mat_index = face_materials_to_matslot[poly_hash]
       
        # create in bmesh
        indices = reversed(vertex_indices[:loop_count])
        bmverts = [used_verts[y] for y in indices]
        
        try:
            face = bm.faces.new(bmverts)
            face.smooth = True
            
            # layers
            for y, inv_y in zip(range(loop_count), reversed(range(loop_count))):
                face.loops[y][vc_layer] = vertex_colors[inv_y]
                face.loops[y][uv_layer].uv = uvs[inv_y]
            
            # set material
            face.material_index = mat_index

        except Exception as e:
            print(e)
        
        
    # finish off
    bm.normal_update()
    bm.to_mesh(me)
    file.seek(mesh_end_file_location)
    
    # cleanup
    bm.free()
    
    return ob
    
    
def load(operator,
         context,
         filepath=""
         ):

    print("importing Mesh: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # import mesh
    file = open(filepath, 'rb')
    
    #
    shared_matdict = {}
    is_psx = filepath.lower().endswith(".psm")
    
    load_mesh(file, matdict = shared_matdict, psx = is_psx)

    # cleanup     
    file.close()
    
    # load textures
    unique_materials = set(shared_matdict.values())
    finalize_mesh_materials_stage1(filepath, unique_materials)
    finalize_mesh_materials_stage2(filepath, unique_materials)
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
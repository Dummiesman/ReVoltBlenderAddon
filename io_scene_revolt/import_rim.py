import bpy
import bmesh
import struct, math, time
from mathutils import Vector

import io_scene_revolt.common_helpers as common

######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath="",
         merge_vertices=True
         ):

    print("importing Mirror Planes: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # import planes
    file = open(filepath, 'rb')
    
    # read planes
    num_mirrors = struct.unpack("<H", file.read(2))[0]
    for x in range(num_mirrors):
        # read data
        file.seek(44, 1) # seek past flags, plane, and bbox
        
        mirror_verts = []
        for y in range(4):
            mirror_vert = Vector(struct.unpack("<fff", file.read(12))) / common.RV_SCALE
            mirror_verts.append(common.vec3_to_blender(mirror_vert))
    
        # create object
        scn = bpy.context.scene  
        
        me = bpy.data.meshes.new("MirrorPlane")
        ob = bpy.data.objects.new("MirrorPlane", me)
        bm = bmesh.new()
        
        scn.collection.objects.link(ob)
        
        # add mesh data
        bmverts = []
        for y in range(4):
            bmverts.append(bm.verts.new(mirror_verts[y]))
        bm.faces.new(bmverts)
        
        bm.to_mesh(me)
        bm.free()

    # cleanup
    file.close()
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
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
         filepath=""
         ):

    print("importing Hull: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # import collision
    file = open(filepath, 'rb')
    
    # create materials to be used on our objects
    hul_material = common.create_colored_material("Hull", (0.8, 0.35, 0.8, 0.8))
    sph_material = common.create_colored_material("HullSphere", (0.35, 0.8, 0.35, 1.0))
    
    # read convex hulls
    chull_count = struct.unpack("<H", file.read(2))[0]
    for x in range(chull_count):
        vert_count, edge_count, face_count = struct.unpack("<HHH", file.read(6))
        file.seek(36, 1) # we don't need the rest of this data
        
        verts = []
        for y in range(vert_count):
            vert = common.vec3_to_blender(struct.unpack("<fff", file.read(12)))
            vert = Vector(vert) / common.RV_SCALE
            verts.append(vert)

        file.seek((4 * edge_count) + (16 * face_count), 1) # seek past face and edge we don't need this
            
        # create hull
        scn = bpy.context.scene
        
        me = bpy.data.meshes.new("Hull")
        ob = bpy.data.objects.new("Hull", me)
        ob.data.materials.append(hul_material)
        ob.show_wire = True
        ob.show_all_edges = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        
        scn.collection.objects.link(ob)
        
        # v
        for vert in verts:
            bm.verts.new(vert)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        
        # calculate normals
        bm.normal_update()
        
        # free resources
        bm.to_mesh(me)
        bm.free()
         
    # read spheres
    sphere_count = struct.unpack("<H", file.read(2))[0]
    
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, diameter=1)
    for face in bm.faces:
        face.smooth = True

    me = bpy.data.meshes.new("HullSphere")
    bm.to_mesh(me)
    bm.free()
    
    for x in range(sphere_count):
        center = common.vec3_to_blender(struct.unpack("<fff", file.read(12)))
        center = Vector(center) / common.RV_SCALE
        
        radius = struct.unpack("<f", file.read(4))[0] / common.RV_SCALE

        ob = bpy.data.objects.new("HullSphere", me)
        ob.data.materials.append(sph_material)
        
        scn = bpy.context.scene
        scn.collection.objects.link(ob)
        
        ob.scale = [radius, radius, radius]
        ob.location = center
    
    # cleanup
    file.close()
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
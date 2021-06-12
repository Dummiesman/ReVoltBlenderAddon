import time, struct, sys, math
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_transform=True,
         selected_only=False
         ):
    
    print("exporting Mirror Planes: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get objs
    objs = bpy.context.selected_objects if selected_only else common.find_objects_by_name("MirrorPlane")
    objs = [x for x in objs if x.type == 'MESH']

    if len(objs) == 0:
        raise Exception("Didn't find any valid objects to export")
    
    # export mirror planes
    file = open(filepath, 'wb')
    
    # create meshes for planes and calculate plane count
    plane_count = 0
    plane_meshes = []
    for ob in objs:
        # get bmesh
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        
        # transform vertices
        if apply_transform:
            common.bm_to_world(bm, ob)
        for vert in bm.verts:
            vert.co *= common.RV_SCALE
        
        # make faces planar
        bmesh.ops.planar_faces(bm, faces=bm.faces, iterations=16, factor=1.0)
        
        # count faces
        for face in bm.faces:
            if len(face.loops) == 4:
                plane_count += 1

        plane_meshes.append(bm)
    
    #
    if plane_count == 0:
        raise Exception("Didn't find any valid faces to export")
        
    # write mirror planes
    file.write(struct.pack("<H", plane_count))
    for bm in plane_meshes:
        for face in bm.faces:
            if len(face.loops) != 4:
                continue

            # flags
            file.write(struct.pack("<L", 1))
            
            # plane
            main_normal = face.normal.normalized()
            main_pos = face.verts[0].co
            main_distance = -main_normal.dot(main_pos)
            
            file.write(struct.pack("<4f", *common.vec3_to_revolt(main_normal), main_distance))
            
            # bounds
            poly_min, poly_max = common.face_bounds_rv(face)

            file.write(struct.pack("<ff", poly_min[0], poly_max[0]))
            file.write(struct.pack("<ff", poly_min[1], poly_max[1]))
            file.write(struct.pack("<ff", poly_min[2], poly_max[2]))
            
            # verts
            for loop in face.loops:
                vert = common.vec3_to_revolt(loop.vert.co)
                file.write(struct.pack("<fff", *vert))
                
            
        bm.free()
        
    # cleanup
    file.close()

    # export complete
    print(" exported " + str(plane_count) + " faces")
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

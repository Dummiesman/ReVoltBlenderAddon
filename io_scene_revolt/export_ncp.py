import time, struct, sys, math
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common
import io_scene_revolt.common_ncp as ncpcommon
from io_scene_revolt.collisiongrid import CollisionGrid, CollisionBucket

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         apply_transform=False,
         selected_only=False,
         generate_grid=False,
         grid_size = 1024
         ):
    
    print("exporting Collision: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get objs
    objs = bpy.context.selected_objects if selected_only else bpy.data.objects
    objs = [x for x in objs if x.type == 'MESH']

    if len(objs) == 0:
        raise Exception("Didn't find any valid objects to export")
    
    # create a joined mesh of all of these
    bm = bmesh.new()
    bm_material_map = []           
    bm_typebits_map = []
    valid_face_count = 0
    
    for ob in objs:
        tempmesh = bpy.data.meshes.new("temp") # create a temporary mesh
        bmtemp = bmesh.new() # temporary mesh to add to the bm
        bmtemp.from_mesh(ob.data) # fill temp mesh with object data
        common.prepare_bmesh(bmtemp)
        
        # copy out things to the maps
        fm_layer = bmtemp.faces.layers.face_map.verify()
        for face in bmtemp.faces:
            material = common.get_material_from_material_slot(ob, face.material_index)
            ncp_id = ncpcommon.get_ncp_id_from_material(material)
            bm_material_map.append(ncp_id)
            if ncp_id is not None:
                valid_face_count += 1
            
            fm_index = face[fm_layer]
            ncp_type = 0
            if fm_index >= 0:
                fm_name = ob.face_maps[fm_index].name
                if fm_name == ncpcommon.FACEMAP_CAMERA_ONLY:
                    ncp_type |= common.COLL_FLAG_CAMERA_ONLY
                elif fm_name == ncpcommon.FACEMAP_OBJECT_ONLY:
                    ncp_type |= common.COLL_FLAG_OBJECT_ONLY
            bm_typebits_map.append(ncp_type)
            
        # apply scale, position and rotation
        for vert in bmtemp.verts:
            if apply_transform:
                vert.co = ob.matrix_world @ vert.co
            vert.co *= common.RV_MESH_SCALE
        
        bmtemp.to_mesh(tempmesh) # save temp bmesh into mesh
        bmtemp.free()
        bm.from_mesh(tempmesh) # add temp mesh to the big mesh
        bpy.data.meshes.remove(tempmesh) # delete tempmesh from scene
        
    bm.faces.ensure_lookup_table()
    
    if valid_face_count == 0:
        bm.free()
        raise Exception("Found no faces with NCP materials")
        
    # export collision
    file = open(filepath, 'wb')
    
    # write polys
    file.write(struct.pack("<H", valid_face_count))
    for face in bm.faces:
        # material and flags
        ncp_material = bm_material_map[face.index]
        if ncp_material is None:
            continue
        
        vertex_count = len(face.verts)
        ncp_type = 1 if vertex_count >= 4 else 0
        ncp_type |= bm_typebits_map[face.index]
        
        # write type and surface
        file.write(struct.pack("<Ll", ncp_type, ncp_material))
        
        # main plane
        main_normal = face.normal.normalized()
        main_pos = face.verts[0].co
        main_distance = -main_normal.dot(main_pos)
        
        file.write(struct.pack("<4f", *common.vec3_to_revolt(main_normal), main_distance))
        
        # other planes
        for x in range(vertex_count - 1, -1, -1):
            x2 = (x - 1) % vertex_count
        
            vert_a = face.verts[x].co
            vert_b = face.verts[x2].co
            vert_delta = vert_b - vert_a
            
            plane_normal = main_normal.cross(vert_delta).normalized()
            plane_distance = -plane_normal.dot(vert_a)
            
            file.write(struct.pack("<4f", *common.vec3_to_revolt(plane_normal), plane_distance))
        
        # plane 5
        if vertex_count < 4:
            file.write(struct.pack("<4f", 0, 0, 0, 0))
        
        # bounds
        poly_min, poly_max = common.face_bounds_rv(face)

        file.write(struct.pack("<ff", poly_min[0], poly_max[0]))
        file.write(struct.pack("<ff", poly_min[1], poly_max[1]))
        file.write(struct.pack("<ff", poly_min[2], poly_max[2]))
            
    # create and write grid
    if generate_grid:
        grid = CollisionGrid(grid_size)
        grid.make_from_bmesh(bm)
        grid.merge_neighbouring_buckets()
        
        # finally, write it
        file.write(struct.pack("<ff", grid.bnds_min[0], grid.bnds_min[2]))
        file.write(struct.pack("<ff", grid.width_sections, grid.depth_sections))
        file.write(struct.pack("<f", grid.size))
        
        for bucket in grid.buckets:
            face_list = bucket.final_indices
            bucket_size = len(face_list)
            
            file.write(struct.pack("<L", bucket_size))
            for idx in face_list:
                file.write(struct.pack("<L", idx))
        
    # cleanup
    bm.free()
    file.close()

    # export complete
    print(" exported " + str(valid_face_count) + " faces")
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

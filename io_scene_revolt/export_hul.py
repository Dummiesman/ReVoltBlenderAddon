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
         apply_modifiers=True,
         apply_transform=True
         ):
    
    print("exporting Hull: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get objs
    hull_objs = bpy.context.selected_objects
    hull_objs = [x for x in hull_objs if x.type == 'MESH']
    sphere_objs = common.find_objects_by_name("HullSphere")
    
    if len(hull_objs) == 0:
        raise Exception("Select the convex hull mesh(es) before exporting")
    
    # export collision
    file = open(filepath, 'wb')
    
    # write chulls
    file.write(struct.pack("<H", len(hull_objs)))
    for ob in hull_objs:
        # create temp mesh
        temp_mesh = None
        if apply_modifiers:
            dg = bpy.context.evaluated_depsgraph_get()
            eval_obj = ob.evaluated_get(dg)
            temp_mesh = eval_obj.to_mesh()
        else:
            temp_mesh = ob.to_mesh()
        
        # get bmesh
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
    
        # export
        bm.verts.ensure_lookup_table()
        verts = []
        vert_remap = {}
        
        # apply transform
        for vert in bm.verts:
            if apply_transform:
                vert.co = ob.matrix_world @ vert.co
            vert.co *= common.RV_SCALE
        
        # gather non-loose vertices
        for vert in bm.verts:
            if not vert.is_wire:
                remap_index = len(verts)
                vert_remap[vert.index] = remap_index
                verts.append(vert)
        
        bnds_min, bnds_max = common.bounds_scaled_rv(ob, common.RV_SCALE, not apply_transform)
        
        # write hull
        file.write(struct.pack("<HHH", len(verts), len(bm.edges), len(bm.faces)))
        
        file.write(struct.pack("<ff", bnds_min[0], bnds_max[0]))
        file.write(struct.pack("<ff", bnds_min[1], bnds_max[1]))
        file.write(struct.pack("<ff", bnds_min[2], bnds_max[2]))
        
        center = ((bnds_min[0] + bnds_max[0]) / 2, (bnds_min[1] + bnds_max[1]) / 2, (bnds_min[2] + bnds_max[2]) / 2)
        file.write(struct.pack("<fff", *center))
        
        
        for vert in verts:
            file.write(struct.pack("<fff", *common.vec3_to_revolt(vert.co)))
            
        for edge in bm.edges:
            if not edge.is_wire:
                i0 = vert_remap[edge.verts[0].index]
                i1 = vert_remap[edge.verts[1].index]
                
                file.write(struct.pack("<HH", i0, i1))
                
        for face in bm.faces:
            normal = face.normal
            dist = -normal.dot(face.verts[0].co)
            
            file.write(struct.pack("<fff", *common.vec3_to_revolt(normal)))
            file.write(struct.pack("<f", dist))
                
        # cleanup
        bm.free()
        
    # write spheres
    file.write(struct.pack("<H", len(sphere_objs)))
    for sph in sphere_objs:
        location = common.vec3_to_revolt(sph.location)
        radius = ((sph.scale[0] + sph.scale[1] + sph.scale[2]) / 3) * common.RV_SCALE
        
        file.write(struct.pack("<fff", location[0] * common.RV_SCALE, location[1] * common.RV_SCALE, location[2] * common.RV_SCALE))
        file.write(struct.pack("<f", radius))
    
    # cleanup
    file.close()

    # export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

import bpy
import bmesh
import struct, math, time
from mathutils import Vector

import io_scene_revolt.common_helpers as common
import io_scene_revolt.common_ncp as ncpcommon

######################################################
# HELPERS
######################################################
# From Huki's Addon: https://gitlab.com/re-volt/re-volt-addon/-/blob/master/io_revolt/ncp_in.py#L27
def intersect(d1, n1, d2, n2, d3, n3):
    """ Intersection of three planes
    "If three planes are each specified by a point x and a unit normal vec n":
    http://mathworld.wolfram.com/Plane-PlaneIntersection.html """
    det = n1.dot(n2.cross(n3))

    # If det is too small, there is no intersection
    if abs(det) < 1e-100:
        return None

    # Returns intersection point
    return (d1 * n2.cross(n3) +
            d2 * n3.cross(n1) +
            d3 * n1.cross(n2)
            ) / det


######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath="",
         merge_vertices=True
         ):

    print("importing Collision: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # import collision
    file = open(filepath, 'rb')

    # create object
    scn = bpy.context.scene

    me = bpy.data.meshes.new("Collision")
    ob = bpy.data.objects.new("Collision", me)
    bm = bmesh.new()
    fm_layer = bm.faces.layers.face_map.new()
    
    ncpcommon.add_ncp_materials(ob)
    ncpcommon.add_ncp_facemaps(ob)
    scn.collection.objects.link(ob)
    
    # face map
    object_only_facemap_index = -1
    camera_only_facemap_index = -1
    for face_map, index in zip(ob.face_maps, range(len(ob.face_maps))):
        if face_map.name == ncpcommon.FACEMAP_OBJECT_ONLY:
            object_only_facemap_index = index
        elif face_map.name == ncpcommon.FACEMAP_CAMERA_ONLY:
            camera_only_facemap_index = index
            
    # material map
    material_map = {}
    for slot, index in zip(ob.material_slots, range(len(ob.material_slots))):
        ncp_id = ncpcommon.get_ncp_id_from_material(slot.material)
        material_map[ncp_id] = index
        
    # read polyhedrons
    poly_count = struct.unpack("<H", file.read(2))[0]
    for x in range(poly_count):
        ncp_type, ncp_material = struct.unpack("<Ll", file.read(8))
        
        planes = []
        for y in range(5):
            nx, ny, nz, dist = struct.unpack("<ffff", file.read(16))
            planes.append(((nx, ny, nz), dist))
            
        # seek past bounding box
        file.seek(24, 1)
        
        ds = [-(p[1]) for p in planes]
        ns = [Vector((p[0][0], p[0][1], p[0][2])) for p in planes]
        
        verts = []
        # From Huki's Addon: https://gitlab.com/re-volt/re-volt-addon/-/blob/master/io_revolt/ncp_in.py#L69
        if ncp_type & common.COLL_FLAG_QUAD:
            verts.append(intersect(ds[0], ns[0], ds[1], ns[1], ds[2], ns[2]))
            verts.append(intersect(ds[0], ns[0], ds[2], ns[2], ds[3], ns[3]))
            verts.append(intersect(ds[0], ns[0], ds[3], ns[3], ds[4], ns[4]))
            verts.append(intersect(ds[0], ns[0], ds[4], ns[4], ds[1], ns[1]))
            face = (0, 3, 2, 1)
        else:
            verts.append(intersect(ds[0], ns[0], ds[1], ns[1], ds[2], ns[2]))
            verts.append(intersect(ds[0], ns[0], ds[2], ns[2], ds[3], ns[3]))
            verts.append(intersect(ds[0], ns[0], ds[3], ns[3], ds[1], ns[1]))
            face = (0, 2, 1)
        
        # no intersection
        if None in verts:
            continue
        
        # transform verts
        for x in range(len(verts)):
            vert = verts[x]
            vert /= common.RV_SCALE
            verts[x] = common.vec3_to_blender(vert)
        
        # creates the bmverts and face
        bmverts = []
        for x in face:
            bmverts.append(bm.verts.new(verts[x]))
        face = bm.faces.new(bmverts)
        
        if ncp_material in material_map:
            face.material_index = material_map[ncp_material]
        if ncp_type & common.COLL_FLAG_OBJECT_ONLY:
            face[fm_layer] = object_only_facemap_index
        elif ncp_type & common.COLL_FLAG_CAMERA_ONLY:
            face[fm_layer] = camera_only_facemap_index

    # merge
    if merge_vertices:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    
    # cleanup
    bm.to_mesh(me)
    bm.free()
    file.close()
    
    # import complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
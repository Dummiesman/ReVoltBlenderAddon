import time, struct, sys
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common

######################################################
# EXPORT MAIN FILES
######################################################
def export_mesh(file, ob, bm, env_list, is_world):
    # layers
    uv_layer = bm.loops.layers.uv.verify()
    vc_layer = bm.loops.layers.color.verify()
    
    common.prepare_bmesh(bm)
    bm.verts.ensure_lookup_table()
        
    if is_world:
        # write bounding info for world
        me_bounds_min, me_bounds_max = common.bmesh_bounds_scaled_rv(bm, common.RV_SCALE)
        me_center = ((me_bounds_max[0] + me_bounds_min[0]) / 2, (me_bounds_max[1] + me_bounds_min[1]) / 2, (me_bounds_max[2] + me_bounds_min[2]) / 2)
        me_radius = max(abs(me_bounds_max[0] - me_bounds_min[0]), abs(me_bounds_max[1] - me_bounds_min[1]), abs(me_bounds_max[2] - me_bounds_min[2]))
        
        # center and radius
        file.write(struct.pack("<fff", *me_center))
        file.write(struct.pack("<f", me_radius))
        
        # bounds
        file.write(struct.pack("<ff", me_bounds_min[0], me_bounds_max[0]))
        file.write(struct.pack("<ff", me_bounds_min[1], me_bounds_max[1]))
        file.write(struct.pack("<ff", me_bounds_min[2], me_bounds_max[2]))
        
    # polygon and vertex counts
    file.write(struct.pack("<HH", len(bm.faces), len(bm.verts)))

    # cache material info for faster export
    # list of (material, principled, texnum)
    default_material_info = (None, None, -1)
    material_info = []
    for x in range(len(ob.material_slots)):
        mat = ob.material_slots[x].material
        principled = common.get_principled_from_material(mat)
        texnum = common.get_texnum_from_material(mat)

        material_info.append((mat, principled, texnum))

    # write faces
    for face in bm.faces:        
        # get flags
        face_type = 1 if len(face.loops) == 4 else 0
        material, principled, texnum = material_info[face.material_index] if face.material_index >= 0 else default_material_info
        
        if material is not None:
            if not material.use_backface_culling:
                face_type |= common.POLY_FLAG_DOUBLESIDED
            if material.blend_method == 'HASHED' or material.blend_method == 'BLEND':
                face_type |= common.POLY_FLAG_TRANSLUCENT
            if material.use_screen_refraction:
                face_type |= common.POLY_FLAG_MIRROR

        # principled data
        spec_amount = 0.0
        alpha_amount = 1.0
        
        if principled is not None:
            # env flag
            spec_input = principled.inputs["Specular"]
            spec_links = spec_input.links
            if is_world and len(spec_links) > 0 and spec_links[0].from_node.type == 'RGB':
                rgb_node = spec_links[0].from_node
                rgb_value = tuple(rgb_node.outputs[0].default_value)
                
                face_type |= common.POLY_FLAG_ENABLEENV
                env_color = rgb_value
                env_list.append(env_color)
            elif not is_world and (spec_input.default_value <= 0.01 and len(spec_links) == 0):
                face_type |= common.POLY_FLAG_DISABLEENV
            
            # translucent amount
            alpha_amount = principled.inputs["Alpha"].default_value
        
        # write
        file.write(struct.pack("<Hh", face_type, texnum)) # Face Type, Tex Num
        
        # Indices
        for loop in reversed(face.loops):
            index = loop.vert.index
            file.write(struct.pack("<H", index))
        if not (face_type & common.POLY_FLAG_QUAD):
            file.write(struct.pack("<H", 0)) # index 4
        
        # Colors
        for loop in reversed(face.loops):
            color = loop[vc_layer]

            if face_type & common.POLY_FLAG_TRANSLUCENT:
                color = (color[0], color[1], color[2], alpha_amount)
            
            rvcolor = common.to_rv_color(color) 
            file.write(struct.pack("<BBBB", *rvcolor))
        if not (face_type & common.POLY_FLAG_QUAD):
            file.write(struct.pack("<L", 0)) # color 4
            
        # UVs
        for loop in reversed(face.loops):
            uv = loop[uv_layer].uv
            file.write(struct.pack("<ff", *common.vec2_to_revolt(uv)))
        if not (face_type & common.POLY_FLAG_QUAD):
            file.write(struct.pack("<ff", 0, 0)) # uv 4
        
    # write vertices
    for vert in bm.verts:
        vert_revolt = mathutils.Vector((common.vec3_to_revolt(vert.co))) * common.RV_SCALE
        
        file.write(struct.pack("<fff", vert_revolt[0], vert_revolt[1], vert_revolt[2]))
        file.write(struct.pack("<fff", *common.vec3_to_revolt(vert.normal)))
    

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         apply_transform=True
         ):
    
    print("exporting Mesh: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get obj
    obj = context.active_object
    if not obj:
        raise Exception("An object was not selected for exporting")

    # export mesh
    file = open(filepath, 'wb')
    
    temp_mesh = None
    if apply_modifiers:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(dg)
        temp_mesh = eval_obj.to_mesh()
    else:
        temp_mesh = obj.to_mesh()
        
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)
    
    if apply_transform:
        common.bm_to_world(bm, obj)
        
    export_mesh(file, obj, bm, None, False)
    
    # cleanup
    bm.free()
    file.close()

    # export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

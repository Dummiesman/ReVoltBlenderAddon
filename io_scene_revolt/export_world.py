import time, struct, sys
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common

######################################################
# EXPORT HELPERS
######################################################
def get_principled_from_material_slot(ob, slotnum):
    if len(ob.material_slots) == 0:
        return None
        
    slot = ob.material_slots[slotnum]
    if slot.material is None:
        return None
    
    tree = slot.material.node_tree.nodes if slot.material.node_tree is not None else []    
    for node in tree:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None
    
def get_material_from_material_slot(ob, slotnum):
    if len(ob.material_slots) == 0:
        return None
        
    slot = ob.material_slots[slotnum]
    return slot.material
    
######################################################
# EXPORT MAIN FILES
######################################################
def export_w_mesh(file, ob, bm, env_list):
    # layers
    uv_layer = bm.loops.layers.uv.active
    vc_layer = bm.loops.layers.color.active
    
    common.prepare_bmesh(bm)
    bm.verts.ensure_lookup_table()

    ob_bounds = common.bounds_scaled(ob, common.RV_LEVEL_SCALE)
    ob_bounds_min = common.vec3_to_revolt((ob_bounds.x.min, ob_bounds.y.min, ob_bounds.z.min))
    ob_bounds_max = common.vec3_to_revolt((ob_bounds.x.max, ob_bounds.y.max, ob_bounds.z.max))
    ob_center = ((ob_bounds_max[0] + ob_bounds_min[0]) / 2, (ob_bounds_max[1] + ob_bounds_min[1]) / 2, (ob_bounds_max[2] + ob_bounds_min[2]) / 2)
    ob_radius = max(abs(ob_bounds_max[0] - ob_bounds_min[0]), abs(ob_bounds_max[1] - ob_bounds_min[1]), abs(ob_bounds_max[2] - ob_bounds_min[2]))
    
    # center and radius
    file.write(struct.pack("<fff", *ob_center))
    file.write(struct.pack("<f", ob_radius))
    
    # bounds
    file.write(struct.pack("<ff", ob_bounds_min[0], ob_bounds_max[0]))
    file.write(struct.pack("<ff", ob_bounds_min[1], ob_bounds_max[1]))
    file.write(struct.pack("<ff", ob_bounds_min[2], ob_bounds_max[2]))
    
    # polygon and vertex counts
    file.write(struct.pack("<HH", len(bm.faces), len(bm.verts)))
    
    # write faces
    for face in bm.faces:        
        # get flags
        face_type = 1 if len(face.loops) == 4 else 0
        
        material = get_material_from_material_slot(ob, face.material_index)
        if material is not None:
            if not material.use_backface_culling:
                face_type |= common.POLY_FLAG_DOUBLESIDED
            if material.blend_method == 'HASHED' or material.blend_method == 'BLEND':
                face_type |= common.POLY_FLAG_TRANSLUCENT
                
        # principled data
        principled = get_principled_from_material_slot(ob, face.material_index)
        spec_amount = 0.0
        alpha_amount = 1.0
        
        if principled is not None:
            # env flag
            spec_amount = principled.inputs["Specular"].default_value
            if spec_amount > 0.01:
                face_type |= common.POLY_FLAG_ENABLEENV
                env_color = (1,1,1,spec_amount) # TODO
                env_list.append(env_color)
            
            # translucent amount
            alpha_amount = principled.inputs["Alpha"].default_value
        
        # get texnum
        texnum = common.get_texnum_from_material(material)
        
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
            color = (1,1,1,1)
            if vc_layer is not None:
                color = loop[vc_layer]
            if face_type & common.POLY_FLAG_TRANSLUCENT:
                color = (color[0], color[1], color[2], alpha_amount)
            
            rvcolor = common.to_rv_color(color) 
            file.write(struct.pack("<BBBB", *rvcolor))
        if not (face_type & common.POLY_FLAG_QUAD):
            file.write(struct.pack("<L", 0)) # color 4
            
        # UVs
        for loop in reversed(face.loops):
            uv = (0,0)
            if uv_layer is not None:
                uv = loop[uv_layer].uv
            file.write(struct.pack("<ff", *common.vec2_to_revolt(uv)))
        if not (face_type & common.POLY_FLAG_QUAD):
            file.write(struct.pack("<ff", 0, 0)) # uv 4
        
    # write vertices
    for vert in bm.verts:
        vert_revolt = mathutils.Vector((common.vec3_to_revolt(ob.matrix_world @ vert.co))) * common.RV_LEVEL_SCALE
        file.write(struct.pack("<fff", vert_revolt[0], vert_revolt[1], vert_revolt[2]))
        file.write(struct.pack("<fff", *common.vec3_to_revolt(vert.normal)))
    

def export_w(file, objs, apply_modifiers):
    # env color list, filled by export_w_mesh
    env_list = []
    
    # mesh count
    file.write(struct.pack('<L', len(objs)))

    # write meshes
    for ob in objs:
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
        export_w_mesh(file, ob, bm, env_list)
        
        # cleanup
        bm.free()

    # write FunnyBall
    scene_min = [float('inf'),float('inf'),float('inf')]
    scene_max = [float('-inf'),float('-inf'),float('-inf')]
    for ob in objs:
        ob_bounds = common.bounds_scaled(ob, common.RV_LEVEL_SCALE)
        ob_bounds_min = common.vec3_to_revolt((ob_bounds.x.min, ob_bounds.y.min, ob_bounds.z.min))
        ob_bounds_max = common.vec3_to_revolt((ob_bounds.x.max, ob_bounds.y.max, ob_bounds.z.max))
    
        scene_min[0] = min(scene_min[0], ob_bounds_min[0])
        scene_min[1] = min(scene_min[1], ob_bounds_min[1])
        scene_min[2] = min(scene_min[2], ob_bounds_min[2])
        
        scene_max[0] = max(scene_max[0], ob_bounds_max[0])
        scene_max[1] = max(scene_max[1], ob_bounds_max[1])
        scene_max[2] = max(scene_max[2], ob_bounds_max[2])
    
    scene_radius = max(abs(scene_max[0] - scene_min[0]), abs(scene_max[1] - scene_min[1]), abs(scene_max[2] - scene_min[2]))
    scene_center = ((scene_max[0] + scene_min[0]) / 2, (scene_max[1] + scene_min[1]) / 2, (scene_max[2] + scene_min[2]) / 2)
    
    file.write(struct.pack('<L', 1)) # 1 funnyball

    file.write(struct.pack('<fff', *scene_center))
    file.write(struct.pack('<f', scene_radius))
    
    # FunnyBall Mesh List
    file.write(struct.pack('<L', len(objs))) # mesh count
    for x in range(len(objs)):
        file.write(struct.pack('<L', x)) # mesh index
    
    # Unk List
    file.write(struct.pack('L', 0)) # 0 unklist
    
    # Env List
    for color in env_list:
        rvcolor = common.to_rv_color(color) 
        file.write(struct.pack("<BBBB", *rvcolor))
    
    file.close()
    return


######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         selected_only=False
         ):
    
    print("exporting World: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get objs
    objs = bpy.context.selected_objects if selected_only else bpy.data.objects
    objs = [x for x in objs if x.type == 'MESH']

    if len(objs) == 0:
        raise Exception("Didn't find any valid objects to export")
        
    # write w
    file = open(filepath, 'wb')
    export_w(file, objs, apply_modifiers)

    # world export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

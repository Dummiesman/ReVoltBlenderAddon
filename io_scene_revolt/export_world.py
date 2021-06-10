import time, struct, sys
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         selected_only=False
         ):
    
    import io_scene_revolt.export_mesh as export_mesh
    print("exporting World: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # get objs
    objs = bpy.context.selected_objects if selected_only else bpy.data.objects
    objs = [x for x in objs if x.type == 'MESH']

    if len(objs) == 0:
        raise Exception("Didn't find any valid objects to export")
        
    # export world
    file = open(filepath, 'wb')
    
    # env color list, filled by export_mesh
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
        export_mesh.export_mesh(file, ob, bm, env_list, True, True)
        
        # cleanup
        bm.free()

    # write FunnyBall
    scene_min = [float('inf'),float('inf'),float('inf')]
    scene_max = [float('-inf'),float('-inf'),float('-inf')]
    for ob in objs:
        ob_bounds_min, ob_bounds_max = common.bounds_scaled_rv(ob, common.RV_SCALE)
        for x in range(3):
            scene_min[x] = min(scene_min[x], ob_bounds_min[x])
            scene_max[x] = max(scene_max[x], ob_bounds_max[x])
    
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

    # export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

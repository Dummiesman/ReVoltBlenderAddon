import time, struct, sys, math
import bpy, bmesh, mathutils
from mathutils import Vector

import io_scene_revolt.common_helpers as common
from io_scene_revolt.bmsplit import BMeshSplitter

######################################################
# HELPERS
######################################################
def bounds_intersect(amin, amax, bmin, bmax):
    return amin[0] <= bmax[0] and amax[0] >= bmin[0] and amin[1] <= bmax[1] and amax[1] >= bmin[1]

 
def prep_bigcube_data(mesh_list):
    scene_min = [float('inf'),float('inf'),float('inf')]
    scene_max = [float('-inf'),float('-inf'),float('-inf')]
    ob_bounds_all = []
    
    for ob, meshes, indices in mesh_list:
        ob_bounds = common.bounds_scaled(ob, common.RV_SCALE)
        ob_bounds_min, ob_bounds_max = ob_bounds
        ob_bounds_all.append(ob_bounds)
        
        for x in range(3):
            scene_min[x] = min(scene_min[x], ob_bounds_min[x])
            scene_max[x] = max(scene_max[x], ob_bounds_max[x])
    
    scene_size_x = scene_max[0] - scene_min[0]
    scene_size_y = scene_max[1] - scene_min[1]
    
    print("scene size " + str(scene_size_x) + "/" + str(scene_size_y))
    
    bcubes_x = math.ceil(scene_size_x  / common.BCUBE_SIZE)
    bcubes_y = math.ceil(scene_size_y / common.BCUBE_SIZE)
    print("bcubes " + str(bcubes_x) + "/" + str(bcubes_y))
    
    bcube_size_x = scene_size_x / bcubes_x
    bcube_size_y = scene_size_y / bcubes_y
    print("bcubes sx " + str(bcube_size_x) + "/" + str(bcube_size_y))
    
    return ((scene_min, scene_max), ob_bounds_all, (bcubes_x, bcubes_y), (bcube_size_x, bcube_size_y))
        

def make_single_bigcube(mesh_list):
    scene_bounds, ob_bounds_all, bcubes_dim, bcubes_size = prep_bigcube_data(mesh_list)
    scene_min, scene_max = scene_bounds
    
    scene_center = ((scene_min[0] + scene_max[0]) / 2,
                    (scene_min[1] + scene_max[1]) / 2,
                    (scene_min[2] + scene_max[2]) / 2)
    scene_radius = max(abs(scene_max[0] - scene_min[0]),
                       abs(scene_max[1] - scene_min[1]),
                       abs(scene_max[2] - scene_min[2]))

    total_indices = []
    for ob, meshes, indices in mesh_list:
        total_indices += indices

    return [(total_indices, scene_bounds, scene_center, scene_radius)]


def make_multi_bigcube(mesh_list):
    bcubes = []
    
    scene_bounds, ob_bounds_all, bcubes_dim, bcubes_size = prep_bigcube_data(mesh_list)
    scene_min, scene_max = scene_bounds
    bcubes_x, bcubes_y = bcubes_dim
    bcube_size_x, bcube_size_y = bcubes_size
    
    # Re-Volt stores game data in the cube structures
    # using the same index twice will result in crashing due to deallocation stuff
    already_used_meshes = set()

    for y in range(bcubes_y):
        for x in range(bcubes_x):
            bcube_bounds_min = [scene_min[0] + (bcube_size_x * x),       scene_min[1] + (bcube_size_y * y),       float('inf')]
            bcube_bounds_max = [scene_min[0] + (bcube_size_x * (x + 1)), scene_min[1] + (bcube_size_y * (y + 1)), float('-inf')]
            
            # find intersecting meshes
            intersecting_indices = []
            for ob, meshes, indices in mesh_list:
                for mesh, index in zip(meshes, indices):
                    if index in already_used_meshes:
                        continue
                        
                    bm_bounds_min, bm_bounds_max = common.bmesh_bounds_scaled(mesh, common.RV_SCALE)
                    if not bounds_intersect(bm_bounds_min, bm_bounds_max, bcube_bounds_min, bcube_bounds_max):
                        continue
                    
                    # add to index list, this intersects
                    intersecting_indices.append(index)
                    already_used_meshes.add(index)
                    
                    # size down cube vertical bounds to fit the mesh
                    bcube_bounds_min[2] = min(bm_bounds_min[2], bcube_bounds_min[2])
                    bcube_bounds_max[2] = max(bm_bounds_max[2], bcube_bounds_max[2])
            
            # get center and radius
            bcube_center = ((bcube_bounds_max[0] + bcube_bounds_min[0]) / 2, 
                            (bcube_bounds_max[1] + bcube_bounds_min[1]) / 2, 
                            (bcube_bounds_max[2] + bcube_bounds_min[2]) / 2)
                            
            bcube_radius = max(abs(bcube_bounds_max[0] - bcube_bounds_min[0]), 
                               abs(bcube_bounds_max[1] - bcube_bounds_min[1]),
                               abs(bcube_bounds_max[2] - bcube_bounds_min[2]))

            if len(intersecting_indices) > 0:
                bcubes.append((intersecting_indices, (bcube_bounds_min, bcube_bounds_max), bcube_center, bcube_radius))
    
    return bcubes    

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         selected_only=False,
         split=False,
         split_size=4096
         ):
    
    import io_scene_revolt.export_mesh as export_mesh
    print("exporting World: %r..." % (filepath))
    time1 = time.perf_counter()
    wm = bpy.context.window_manager
    wm.progress_begin(0, 1)

    # get objs
    objs = bpy.context.selected_objects if selected_only else bpy.data.objects
    objs = [x for x in objs if x.type == 'MESH']
    ob_count = len(objs)
    
    if ob_count == 0:
        raise Exception("Didn't find any valid objects to export")
        
    # export world
    file = open(filepath, 'wb')
    
    # scale split_size
    split_size /= common.RV_SCALE
    
    # env list, filled by export_mesh
    # mesh_list filled with export data
    env_list = []
    mesh_list = []
    mesh_count = 0

    # prepare meshes
    print(" ... preparing (%.4f)" % (time.perf_counter() - time1))
    for ob in objs:
        # get bmesh
        bm = common.get_bmesh(ob, apply_modifiers = apply_modifiers)
        common.bm_to_world(bm, ob)
        
        # split if requested
        if split:   
            splitter = BMeshSplitter(split_size)
            splits = splitter.split(bm)
        else:
            splits = [bm]
        
        mesh_indices = list(range(mesh_count, mesh_count + len(splits)))
        mesh_count += len(splits)
        mesh_list.append((ob, splits, mesh_indices))
        
    # mesh count
    file.write(struct.pack('<L', mesh_count))

    # write meshes
    print(" ... mesh exporting (%.4f)" % (time.perf_counter() - time1))
    export_counter = 0
    for ob, meshes, indices in mesh_list:
        for mesh in meshes:
            #def export_mesh(file, ob, bm, env_list, is_world):
            export_mesh.export_mesh(file, ob, mesh, env_list, True)
            
        export_counter += 1
        wm.progress_update((export_counter / ob_count) * 0.9)

    # calculate bigcubes
    # we make a single bigcube here if not splitting since we can't guarantee 
    # the user provided meshes are small enough to work properly
    print(" ... bigcube calculation (%.4f)" % (time.perf_counter() - time1))
    bigcubes = make_multi_bigcube(mesh_list) if split else make_single_bigcube(mesh_list)
    
    # write bigcubes
    print(" ... bigcube writing (%.4f)" % (time.perf_counter() - time1))
    file.write(struct.pack('<L', len(bigcubes)))
    for me_indices, bounds, center, radius in bigcubes:
        file.write(struct.pack('<fff', *common.vec3_to_revolt(center)))
        file.write(struct.pack('<f', radius))
        
        file.write(struct.pack('<L', len(me_indices))) # mesh count
        for x in me_indices:
            file.write(struct.pack('<L', x)) # mesh index
    
    wm.progress_update(1.0)
    
    # Texanim List
    print(" ... texanim writing (%.4f)" % (time.perf_counter() - time1))
    file.write(struct.pack('L', 0)) # not supported for now
    
    # Env List
    for color in env_list:
        rvcolor = common.to_rv_color(color) 
        file.write(struct.pack("<BBBB", *rvcolor))
    
    # cleanup
    for ob, meshes, indices in mesh_list:
        for mesh in meshes:
            mesh.free()
    file.close()
    wm.progress_end()

    # export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}

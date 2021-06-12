import bmesh, bpy, mathutils
import math

class BMeshSplitter:
    def __init__(self, split_size):
        self.meshes = []
        self.split_size = split_size

    def split(self, bm):
        """Return a list of bmeshes, may return the original if bounds are smaller than split size"""
        
        # find mesh bounds
        bnds_min = [float('inf'),float('inf'),float('inf')]
        bnds_max = [float('-inf'),float('-inf'),float('-inf')]
        
        for vert in bm.verts:
            vco = vert.co
            for x in range(3):
                bnds_min[x] = min(vco[x], bnds_min[x])
                bnds_max[x] = max(vco[x], bnds_max[x])

        # slightly inflate bounds (otherwise verts right on the edge will overflow)
        for x in range(3):
            bnds_min[x] -= 0.1
            bnds_max[x] += 0.1
         
        # init buckets
        x_size = bnds_max[0] - bnds_min[0]
        y_size = bnds_max[1] - bnds_min[1]
        
        if x_size < self.split_size and y_size < self.split_size:
            self.meshes = [bm]
            return self.meshes
        
        buckets_x = max(1, math.ceil(x_size / self.split_size))
        buckets_y = max(1, math.ceil(y_size / self.split_size))
            
        buckets_size_x = x_size / buckets_x
        buckets_size_y = y_size / buckets_y
        
        buckets_total = buckets_x *  buckets_y
        buckets = []
        for x in range(buckets_total):
            buckets.append([])
        
        # fill buckets
        for face in bm.faces:
            center = face.calc_center_median()
            x_normalized_pos = (center[0] - bnds_min[0]) / x_size
            y_normalized_pos = (center[1] - bnds_min[1]) / y_size
            
            x_bucket = math.floor(x_normalized_pos * buckets_x)
            y_bucket = math.floor(y_normalized_pos * buckets_y)
            
            bucket_index = (y_bucket * buckets_x) + x_bucket
            buckets[bucket_index].append(face)
        
        # prepare bmeshes from buckets
        self.meshes = []
        bm.verts.ensure_lookup_table()
        
        bm_colors = bm.loops.layers.color.items()
        bm_uvs = bm.loops.layers.uv.items()
        
        for bucket in buckets:
            bucket_verts = []
            bucket_vert_remap = {}
            
            # empty
            if len(bucket) == 0:
                continue
            
            # remap verts
            for face in bucket:
                for vert in face.verts:
                    if not vert.index in bucket_vert_remap:
                        bucket_vert_remap[vert.index] = len(bucket_verts)
                        bucket_verts.append(vert)
                        
            # create new bmesh
            bm2 = bmesh.new()
            self.meshes.append(bm2)
            
            # copy layers
            for color_layer in bm_colors:
                bm2.loops.layers.color.new(color_layer[0])
            for uv_layer in bm_uvs:
                bm2.loops.layers.uv.new(uv_layer[0])
            
            # copy verts
            for vert in bucket_verts:
                newvert = bm2.verts.new(vert.co)
                newvert.normal = vert.normal

            bm2.verts.ensure_lookup_table()
            bm2.verts.index_update()
            
            # copy faces
            for face in bucket:
                verts = [bm2.verts[bucket_vert_remap[l.vert.index]] for l in face.loops]
                newface = bm2.faces.new(verts)
                
                # copy properties
                newface.material_index = face.material_index
                newface.smooth = face.smooth
                
                # copy layers
                loop_count = len(face.loops)
                for x in range(loop_count):
                    loop_new = newface.loops[x]
                    loop_old = face.loops[x]
                    
                    for color_layer in bm_colors:
                        color_layer_old = bm.loops.layers.color[color_layer[0]]
                        color_layer_new = bm2.loops.layers.color[color_layer[0]]
                        loop_new[color_layer_new] = loop_old[color_layer_old]
                    for uv_layer in bm_uvs:
                        uv_layer_old = bm.loops.layers.uv[uv_layer[0]]
                        uv_layer_new = bm2.loops.layers.uv[uv_layer[0]]
                        loop_new[uv_layer_new].uv = loop_old[uv_layer_old].uv
            
            bm2.faces.ensure_lookup_table()        
        
        return self.meshes
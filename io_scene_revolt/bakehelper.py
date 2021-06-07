import bpy
import bmesh
import colorsys

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList
                       )
                       
from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       FloatProperty,
                       PointerProperty)
                       
class RVBakeHelper(Operator):
    bl_idname = "rv.bakehelper"
    bl_label = "RV Bake Helper"
    
    min_value: FloatProperty(name="Min Value", default=0, min=0, max=1)
    max_value: FloatProperty(name="Max Value", default=1, min=0, max=1)
    min_saturation: FloatProperty(name="Min Saturation", default=0, min=0, max=1)
    max_saturation: FloatProperty(name="Max Saturation", default=0, min=0, max=1)
    ambient_value: FloatProperty(name="Ambient", default=0, min=0, max=1)
    smoothing: FloatProperty(name="Quantization", default=0, min=0)
    
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    
    def vertex_key(self, vector):
        step = self.smoothing
        if step > 0.01:
            return (round(vector[0] / step) * step, round(vector[1] / step) * step, round(vector[2] / step) * step)
        else:
            return (vector[0], vector[1], vector[2])

    def execute(self, context):
        scene = context.scene
        
        #BAKE
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.bake(type='DIFFUSE')

        # ENTER EDIT MODE AND FIX COLORS
        ob = context.object
        bpy.ops.object.mode_set(mode = 'EDIT')

        if ob.type == 'MESH':
            # get bmesh
            bm = bmesh.from_edit_mesh(ob.data)
            
            # clamp HSV
            vc_layer = bm.loops.layers.color.active
            for face in bm.faces:
                for loop in face.loops:
                    col = loop[vc_layer]
                    col_hsv = colorsys.rgb_to_hsv(col[0], col[1], col[2])
                    
                    new_s = min(max(self.min_saturation, col_hsv[1]), self.max_saturation)
                    new_v = min(max(self.min_value,col_hsv[2] + self.ambient_value), self.max_value)
                    new_col = colorsys.hsv_to_rgb(col_hsv[0], new_s, new_v)
                    loop[vc_layer] = (*new_col, col[3])
            
            # average vertex colors at location
            colors_count = {}
            colors_sum = {}
            for face in bm.faces:
                for loop in face.loops:
                    col = loop[vc_layer]
                    co = loop.vert.co
                    key = self.vertex_key(co)
                    
                    if not key in colors_count:
                        colors_count[key] = 0
                        colors_sum[key] = [0,0,0]
                        
                    cur_sum = colors_sum[key]
                    colors_sum[key] = [cur_sum[0] + col[0], cur_sum[1] + col[1], cur_sum[2] + col[2]]
                    colors_count[key] += 1
                    
            for face in bm.faces:
                for loop in face.loops:
                    col = loop[vc_layer]
                    co = loop.vert.co
                    key = self.vertex_key(co)
                    
                    colsum = colors_sum[key]
                    colcount = colors_count[key]
                    
                    loop[vc_layer] = (colsum[0] / colcount, colsum[1] / colcount, colsum[2] / colcount, col[3])
                    

            # finish off
            bmesh.update_edit_mesh(ob.data)

        # ENTER VERTEX PAINT MODE FOR PREVEIW
        bpy.ops.object.mode_set(mode = 'VERTEX_PAINT')
        
        return {'FINISHED'}
 

 
    def draw(self, context):
        self.layout.prop(self, "min_value")
        self.layout.prop(self, "max_value")
        self.layout.separator()

        self.layout.prop(self, "min_saturation")
        self.layout.prop(self, "max_saturation")
        self.layout.separator()
        
        self.layout.prop(self, "ambient_value")
        self.layout.prop(self, "smoothing")
 
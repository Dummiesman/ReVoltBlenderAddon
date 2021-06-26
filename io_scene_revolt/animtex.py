import bpy
import bmesh
from bpy.props import (
        CollectionProperty,
        IntProperty,
        PointerProperty,
        FloatVectorProperty
        )

from bpy.types import (
        Material,
        PropertyGroup
        )
        

class TextureAnimationFrame(PropertyGroup):
    # TODO: Use pointerproperty to image instead?
    # problem with that is how2load???
    texture_number: IntProperty(
        name = "Texture Number",
        default = 0,
        min = -1,
        max = 64
        )
        
    delay: IntProperty(
        name = "Delay",
        description="Delay in milliseconds",
        default = 0,
        min = 0
        )
        
    uv0: FloatVectorProperty(
        name = "UV0",
        size = 2
        )
        
    uv1: FloatVectorProperty(
        name = "UV1",
        size = 2
        )
        
    uv2: FloatVectorProperty(
        name = "UV2",
        size = 2
        )
        
    uv3: FloatVectorProperty(
        name = "UV3",
        size = 2
        )
        
    def get_uv(self, index):
        if index < 0 or index > 3:
            return None
        if index == 0:
            return self.uv0
        elif index == 1:
            return self.uv1
        elif index == 2:
            return self.uv2
        elif index == 3:
            return self.uv3
            
    def set_uv(self, index, uv):
        if index < 0 or index > 3:
            return
        if index == 0:
            self.uv0 = uv
        elif index == 1:
            self.uv1 = uv
        elif index == 2:
            self.uv2 = uv
        elif index == 3:
            self.uv3 = uv
    
        
class TextureAnimationSlot(PropertyGroup):
    frames: CollectionProperty(
        name = "Frames",
        type = TextureAnimationFrame
        )
        
    selected_frame: IntProperty(
        name = "Selected Frame",
        default = 0,
        min = 0,
        )
        
    def get_selected_frame(self):
        frames = self.frames
        selected = self.selected_frame
        if selected < len(frames) and selected >= 0:
            return frames[selected]
        else:
            return None

    
class TextureAnimations(PropertyGroup):
    slots: CollectionProperty(
        name = "Slots",
        type = TextureAnimationSlot
        )
        
    selected_slot: IntProperty(
        name = "Selected Slot",
        default = 0,
        min = 0,
        )

    def get_selected_slot(self):
        slots = self.slots
        selected = self.selected_slot
        if selected < len(slots) and selected >= 0:
            return slots[selected]
        else:
            return None
    
    def clear(self):
        self.slots.clear()


def create_temp_mesh(me):
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new()
    
    # add mesh data
    bmverts = []
    for y in range(4):
        bmverts.append(bm.verts.new((0, 0, 0)))
    bm.faces.new(bmverts)
    
    bm.to_mesh(me)
    bm.free()
    
def get_temp_obj():
    if "RV_animtex_tempobject" in bpy.data.objects:
        return bpy.data.objects["RV_animtex_tempobject"]
    else:
        me = bpy.data.meshes.new("RV_animtex_tempmesh")
        create_temp_mesh(me)
        
        return bpy.data.objects.new("RV_animtex_tempobject", me)
    
def edit_temp_ob():
    bpy.context.view_layer.objects.active = get_temp_obj()
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

def register():
    bpy.utils.register_class(TextureAnimationFrame)
    bpy.utils.register_class(TextureAnimationSlot)
    bpy.utils.register_class(TextureAnimations)
    
def unregister():
    bpy.utils.unregister_class(TextureAnimations)
    bpy.utils.unregister_class(TextureAnimationSlot)
    bpy.utils.unregister_class(TextureAnimationFrame)
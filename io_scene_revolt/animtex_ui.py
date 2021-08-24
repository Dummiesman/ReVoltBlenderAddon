import bpy
import os.path as path

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
                       PointerProperty)

# -------------------------------------------------------------------
#   Operators
# -------------------------------------------------------------------
class AddFrameOperator(Operator):
    """Adds a new, blank variant"""
    bl_idname = "revolt.add_texanim_frame"
    bl_label = "Add Frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = bpy.context.scene
        animtex = scene.rv_animtex
        
        slot = animtex.get_selected_slot()
        if slot is not None:
            slot.frames.add()
       
        return {'FINISHED'}
 
 
class DeleteFrameOperator(Operator):
    """Adds a new, blank variant"""
    bl_idname = "revolt.delete_texanim_frame"
    bl_label = "Delete Frame"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = bpy.context.scene
        animtex = scene.rv_animtex
        
        slot = animtex.get_selected_slot()
        if slot is not None:
            slot.frames.remove(slot.selected_frame)

            if slot.selected_frame > 0:
                slot.selected_frame -= 1
       
        return {'FINISHED'}


class AddSlotOperator(Operator):
    """Adds a new, blank variant"""
    bl_idname = "revolt.add_texanim_slot"
    bl_label = "Add Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = bpy.context.scene
        animtex = scene.rv_animtex
        anims = animtex.slots
        
        anims.add()
        animtex.selected_slot = len(anims) - 1
        
        return {'FINISHED'}

 
class CloneSlotOperator(Operator):
    """Duplicates the currently selected slot"""
    bl_idname = "revolt.clone_texanim_slot"
    bl_label = "Clone Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        #scene = context.scene
        #angel = scene.angel
        #
        #current_variant = angel.get_selected_variant()
        #if current_variant is not None:
        #    variant = angel.variants.add()
        #    variant.clone_from(current_variant)
        #    angel.selected_variant = len(angel.variants) - 1
        #
        return {'FINISHED'}


class DeleteSlotOperator(Operator):
    """Deletes the currently selected slot"""
    bl_idname = "revolt.delete_texanim_slot"
    bl_label = "Delete Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = bpy.context.scene
        animtex = scene.rv_animtex
        anims = animtex.slots
        
        if animtex.selected_slot < len(anims):
            anims.remove(animtex.selected_slot)
            
            if animtex.selected_slot > 0:
                animtex.selected_slot -= 1
        
        return {'FINISHED'}


class DeleteSlotConfirmOperator(Operator):
    """Deletes the currently selected variant"""
    bl_idname = "revolt.delete_texanim_slot_confirm"
    bl_label = "Do you really want to delete this slot?"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.revolt.delete_texanim_slot()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
 

class FuckyOperator(Operator):
    """A test"""
    bl_idname = "revolt.texanim_fucky_op"
    bl_label = "Fucky Op Test"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        import io_scene_revolt.animtex as animtex
        animtex.edit_temp_ob()
        
        return {'FINISHED'}
        
# -------------------------------------------------------------------
#   Drawing
# -------------------------------------------------------------------
class REVOLT_PT_AnimsPanel(Panel):
    bl_label = "Re-Volt Texture Animations"
    bl_idname = "REVOLT_PT_anims_panel"
    bl_space_type = "IMAGE_EDITOR"   
    bl_region_type = "UI"
    bl_category = "Re-Volt"
    bl_options = {'DEFAULT_CLOSED'}
    

    @classmethod
    def poll(self,context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        animtex = scene.rv_animtex
        anims = animtex.slots
            
        # AAAH
        # layout.operator("revolt.texanim_fucky_op")
       
        # selected variant 
        layout.prop(animtex, "selected_slot")
        selected_slot = animtex.selected_slot
        
        # draw +/copy/- row
        row = layout.row()
        c1 = row.column()
        c1.label(text=str(len(anims)) + " slots")
        
        c2 = row.column()
        c3 = row.column()
        
        c2row = c2.row(align=True)
        c3row = c3.row(align=True)
        
        
        c3row.operator("revolt.delete_texanim_slot_confirm", text= "", icon='REMOVE')
        c3row.operator("revolt.clone_texanim_slot", text= "", icon='DUPLICATE')
        c3row.operator("revolt.add_texanim_slot", text= "", icon='ADD')
        
        # the rest
        
        layout.separator()
        if selected_slot >= len(anims):
            layout.label(text="Selected slot has not been created yet.")
        else:
            slot = anims[selected_slot]
            frames = slot.frames
            
            row = layout.row()
            c1 = row.column()
            c2 = row.column()
            
            # DRAW COLUMN 1
            c1.label(text="Frames")
            c1.operator("revolt.add_texanim_frame")
            c1.operator("revolt.delete_texanim_frame")
            c1.prop(slot, "selected_frame")
            c1.separator()
            
            for x in range(len(frames)):
                box = c1.box()
                
                bc1 = box.column()
                bc2 = box.column()
                
                if x == slot.selected_frame:
                    bc1.label(text=f"* Frame {x}")
                else:
                    bc1.label(text=f"Frame {x}")
                
                
            # DRAW COLUMN 2
            active_frame = slot.get_selected_frame()
            
            if active_frame is not None:
                c2.prop(active_frame, "texture_number")
                c2.prop(active_frame, "delay")
                c2.prop(active_frame, "uv0")
                c2.prop(active_frame, "uv1")
                c2.prop(active_frame, "uv2")
                c2.prop(active_frame, "uv3")
            else:
                c2.label(text="Selected frame out of range")



# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = (
    FuckyOperator,
    AddSlotOperator,
    CloneSlotOperator,
    DeleteSlotOperator,
    DeleteSlotConfirmOperator,
    AddFrameOperator,
    DeleteFrameOperator,
    REVOLT_PT_AnimsPanel
)

def register():        
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

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
                       
class NCPSetupOperator(Operator):
    bl_idname = "rv.ncpsetup"
    bl_label = "Setup NCP Object"
    
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH'


    def execute(self, context):
        import io_scene_revolt.common_ncp as common_ncp
        ob = context.active_object

        common_ncp.add_ncp_facemaps(ob)
        common_ncp.add_ncp_materials(ob)

        return {'FINISHED'}

 
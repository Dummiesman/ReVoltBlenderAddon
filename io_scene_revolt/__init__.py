bl_info = {
    "name": "Re-Volt",
    "author": "Dummiesman",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Re-Volt files",
    "warning": "*VERY EARLY VERSION WITH ALMOST NO FEATURES*",
    "doc_url": "https://github.com/Dummiesman/ReVoltBlenderAddon/",
    "tracker_url": "https://github.com/Dummiesman/ReVoltBlenderAddon/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

from io_scene_revolt.bakehelper import RVBakeHelper

#class ImportWorld(bpy.types.Operator, ImportHelper):
#    """Import from W file format (.w)"""
#    bl_idname = "import_scene.rvworld"
#    bl_label = 'Import Re-Volt World'
#    bl_options = {'UNDO'}
#
#    filename_ext = ".w"
#    filter_glob: StringProperty(default="*.w", options={'HIDDEN'})
#
#    def execute(self, context):
#        from . import import_world
#        keywords = self.as_keywords(ignore=("axis_forward",
#                                            "axis_up",
#                                            "filter_glob",
#                                            "check_existing",
#                                            ))
#
#        return import_world.load(self, context, **keywords)


class ExportWorld(bpy.types.Operator, ExportHelper):
    """Export to W file format"""
    bl_idname = "export_scene.rvworld"
    bl_label = 'Export Re-Volt World'

    filename_ext = ".w"
    filter_glob: StringProperty(
            default="*.w",
            options={'HIDDEN'},
            )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
        )
        
    selected_only: BoolProperty(
        name="Selection Only",        
        default=False,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "selected_only")
        
    def execute(self, context):
        from . import export_world
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_world.save(self, context, **keywords)


class ExportMesh(bpy.types.Operator, ExportHelper):
    """Export to PRM/M file format"""
    bl_idname = "export_scene.rvmesh"
    bl_label = 'Export Re-Volt Mesh'

    filename_ext = ".m"
    filter_glob: StringProperty(
            default="*.m;*.prm",
            options={'HIDDEN'},
            )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
        )
        
    apply_transform: BoolProperty(
        name="Apply Transform",
        default=False,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "apply_transform")
        
    def execute(self, context):
        from . import export_mesh
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_mesh.save(self, context, **keywords)

# Add to a menu
def menu_func_export(self, context):
    self.layout.separator()
    self.layout.label(text="Re-Volt Addon")
    self.layout.operator(ExportWorld.bl_idname, text="Re-Volt World (.w)")
    self.layout.operator(ExportMesh.bl_idname, text="Re-Volt Mesh (.m/.prm)")

#def menu_func_import(self, context):
#    self.layout.operator(ImportWorld.bl_idname, text="Re-Volt World (.w)")

def menu_func_bake(self, context):
    self.layout.operator(RVBakeHelper.bl_idname)

# Register factories
classes = (
    #ImportWorld,
    ExportWorld,
    ExportMesh,
    RVBakeHelper
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_bake)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func_bake)
    #bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

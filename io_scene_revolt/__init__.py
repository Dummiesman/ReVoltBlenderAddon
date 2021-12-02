bl_info = {
    "name": "Re-Volt",
    "author": "Dummiesman",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Re-Volt files",
    "warning": "Functionally works, but needs more testing. It's possible things may go wrong.",
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
        PointerProperty
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

from io_scene_revolt.bakehelper import RVBakeHelper
from io_scene_revolt.ncpsetup import NCPSetupOperator
import io_scene_revolt.animtex as animtex
import io_scene_revolt.animtex_ui as animtex_ui
import io_scene_revolt.bl_preferences as bl_preferences

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
        
    split: BoolProperty(
        name="Split Exported Meshes",
        default=True,
        )
        
    split_size: FloatProperty(
        name="Split Size",        
        default=4096,
        min=16        
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "selected_only")
        layout.separator()
        sub = layout.row()
        sub.prop(self, "split")
        sub = layout.row()
        sub.enabled = self.split
        sub.prop(self, "split_size")
        
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

    check_extension = False
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

        
class ExportCollision(bpy.types.Operator, ExportHelper):
    """Export to NCP file format"""
    bl_idname = "export_scene.rvcoll"
    bl_label = 'Export Re-Volt Collision'

    filename_ext = ".ncp"
    filter_glob: StringProperty(
            default="*.ncp",
            options={'HIDDEN'},
            )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
        )
        
    apply_transform: BoolProperty(
        name="Apply Transform",
        default=True,
        )
        
    selected_only: BoolProperty(
        name="Selection Only",        
        default=False,
        )
        
    generate_grid: BoolProperty(
        name="Generate Grid",        
        default=False,
        )
        
    grid_size: FloatProperty(
        name="Grid Size",        
        default=1024,
        min=128        
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "apply_transform")
        sub = layout.row()
        sub.prop(self, "selected_only")
        sub = layout.row()
        sub.prop(self, "generate_grid", text="Generate Grid (Required for levels)")
        sub = layout.row()
        sub.enabled = self.generate_grid
        sub.prop(self, "grid_size")
        
    def execute(self, context):
        from . import export_ncp
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_ncp.save(self, context, **keywords)


class ExportHull(bpy.types.Operator, ExportHelper):
    """Export to HUL file format"""
    bl_idname = "export_scene.rvhull"
    bl_label = 'Export Re-Volt Hull'

    filename_ext = ".hul"
    filter_glob: StringProperty(
            default="*.hul",
            options={'HIDDEN'},
            )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
        )
        
    apply_transform: BoolProperty(
        name="Apply Transform",
        default=True,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "apply_transform")
        
    def execute(self, context):
        from . import export_hul
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_hul.save(self, context, **keywords)
        

class ExportMirrors(bpy.types.Operator, ExportHelper):
    """Export to RIM file format"""
    bl_idname = "export_scene.rvmirr"
    bl_label = 'Export Re-Volt Mirrors'

    filename_ext = ".rim"
    filter_glob: StringProperty(
            default="*.rim",
            options={'HIDDEN'},
            )

    apply_transform: BoolProperty(
        name="Apply Transform",
        default=True,
        )
        
    selected_only: BoolProperty(
        name="Selected Only",
        default=False,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_transform")
        sub = layout.row()
        sub.prop(self, "selected_only")
        
    def execute(self, context):
        from . import export_rim
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_rim.save(self, context, **keywords)
        

class ImportWorld(bpy.types.Operator, ImportHelper):
    """Import from W file format"""
    bl_idname = "import_scene.rvworld"
    bl_label = 'Import Re-Volt World'

    filename_ext = ".w"
    filter_glob: StringProperty(
            default="*.w;*.psw",
            options={'HIDDEN'},
            )

       
    def execute(self, context):
        from . import import_world
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return import_world.load(self, context, **keywords)

    
class ImportMesh(bpy.types.Operator, ImportHelper):
    """Import from PRM/M file format"""
    bl_idname = "import_scene.rvmesh"
    bl_label = 'Import Re-Volt Mesh'

    filename_ext = ".m"
    filter_glob: StringProperty(
            default="*.m;*.prm;*.psm",
            options={'HIDDEN'},
            )

       
    def execute(self, context):
        from . import import_mesh
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return import_mesh.load(self, context, **keywords)


class ImportHull(bpy.types.Operator, ImportHelper):
    """Import from HUL file format"""
    bl_idname = "import_scene.rvhull"
    bl_label = 'Import Re-Volt Hull'

    filename_ext = ".hul"
    filter_glob: StringProperty(
            default="*.hul",
            options={'HIDDEN'},
            )

    psx: BoolProperty(
        name="PSX",
        default=False,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.label(text="[WARNING] Make sure to check this when importing PSX hulls.")
        sub = layout.row()
        sub.label(text="failure to do so may cause Blender to crash!")
        sub = layout.row()
        sub.prop(self, "psx")

    def execute(self, context):
        from . import import_hul
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return import_hul.load(self, context, **keywords)

        
class ImportCollision(bpy.types.Operator, ImportHelper):
    """Import from NCP file format"""
    bl_idname = "import_scene.rvcoll"
    bl_label = 'Import Re-Volt Collision'

    filename_ext = ".ncp"
    filter_glob: StringProperty(
            default="*.ncp",
            options={'HIDDEN'},
            )

    merge_vertices: BoolProperty(
        name="Merge Vertices",
        default=True,
        description="Merge vertices for easier editing."
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "merge_vertices")
        
    def execute(self, context):
        from . import import_ncp
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return import_ncp.load(self, context, **keywords)


class ImportMirrors(bpy.types.Operator, ImportHelper):
    """Import from RIM file format"""
    bl_idname = "import_scene.rvmirr"
    bl_label = 'Import Re-Volt Mirrors'

    filename_ext = ".rim"
    filter_glob: StringProperty(
            default="*.rim",
            options={'HIDDEN'},
            )


    def execute(self, context):
        from . import import_rim
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return import_rim.load(self, context, **keywords)


# Add to a menu
def menu_func_export(self, context):
    self.layout.separator()
    self.layout.label(text="Re-Volt Addon")
    self.layout.operator(ExportWorld.bl_idname, text="Re-Volt World (.w)")
    self.layout.operator(ExportMesh.bl_idname, text="Re-Volt Mesh (.m/.prm)")
    self.layout.operator(ExportHull.bl_idname, text="Re-Volt Hull (.hul)")
    self.layout.operator(ExportCollision.bl_idname, text="Re-Volt Collision (.ncp)")
    self.layout.operator(ExportMirrors.bl_idname, text="Re-Volt Mirrors (.rim)")
    self.layout.separator()

def menu_func_import(self, context):
    self.layout.separator()
    self.layout.label(text="Re-Volt Addon")
    self.layout.operator(ImportWorld.bl_idname, text="Re-Volt World (.w/.psw)")
    self.layout.operator(ImportMesh.bl_idname, text="Re-Volt Mesh (.m/.prm/.psm)")
    self.layout.operator(ImportHull.bl_idname, text="Re-Volt Hull (.hul)")
    self.layout.operator(ImportCollision.bl_idname, text="Re-Volt Collision (.ncp)")
    self.layout.operator(ImportMirrors.bl_idname, text="Re-Volt Mirrors (.rim)")
    self.layout.separator()

def menu_func_ops(self, context):
    self.layout.operator(RVBakeHelper.bl_idname)
    self.layout.operator(NCPSetupOperator.bl_idname)

# Register factories
classes = (
    ExportWorld,
    ExportMesh,
    ExportCollision,
    ExportHull,
    ExportMirrors,
    ImportWorld,
    ImportMesh,
    ImportCollision,
    ImportHull,
    ImportMirrors,
    RVBakeHelper,
    NCPSetupOperator
)

def register():
    bl_preferences.register()
    animtex.register()
    animtex_ui.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_ops)
    
    bpy.types.Scene.rv_animtex = PointerProperty(type=animtex.TextureAnimations)


def unregister():
    del bpy.types.Scene.rv_animtex

    bpy.types.VIEW3D_MT_object.remove(menu_func_ops)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    animtex.unregister()
    animtex_ui.unregister()
    bl_preferences.unregister()

if __name__ == "__main__":
    register()

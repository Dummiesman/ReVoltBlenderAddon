import os
import logging
import random

import bpy

class ReVoltPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    scale: bpy.props.FloatProperty(
        name="Scale",
        default=100,
        min=1,
        max=100,
        description="The scaling applied to import/export."
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="The scaling applied to import/export. Blender must be restarted if changed after exporting/importing.")
        layout.prop(self, "scale")


classes = (ReVoltPreferences,)

register_factory, unregister_factory = bpy.utils.register_classes_factory(classes)

def register():
    register_factory()


def unregister():
    unregister_factory()
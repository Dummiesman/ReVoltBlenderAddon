import bpy
import io_scene_revolt.common_helpers as common

class RVExportMaterialInfo:
    def __init__(self, mat, is_world):
        self.alpha = 1.0
        self.is_env = not is_world
        self.env_color = (1,1,1,1)
        self.flags = 0
        self.texnum = common.get_texnum_from_material(mat)
        
        if mat is not None:
            if not mat.use_backface_culling:
                self.flags |= common.POLY_FLAG_DOUBLESIDED
            if mat.blend_method == 'HASHED' or mat.blend_method == 'BLEND':
                self.flags |= common.POLY_FLAG_TRANSLUCENT
            if mat.use_screen_refraction:
                self.flags |= common.POLY_FLAG_MIRROR

        principled = common.get_principled_from_material(mat) 
        principled = common.get_material_node_of_type(mat, 'BSDF_PRINCIPLED')
        if principled is not None:
            # env flag
            spec_input = principled.inputs["Specular"]
            spec_links = spec_input.links
            
            if is_world:
                if len(spec_links) > 0 and spec_links[0].from_node.type == 'RGB':
                    rgb_node = spec_links[0].from_node
                    rgb_value = tuple(rgb_node.outputs[0].default_value)
                    
                    self.flags |= common.POLY_FLAG_ENABLEENV
                    self.env_color = rgb_value
                    self.is_env = True
            else:
                if len(spec_links) == 0 and spec_input.default_value <= 0.01:
                    self.flags |= common.POLY_FLAG_DISABLEENV
                    self.is_env = False
            
            # translucent amount
            self.alpha = principled.inputs["Alpha"].default_value

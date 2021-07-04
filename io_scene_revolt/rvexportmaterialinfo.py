import bpy
import io_scene_revolt.common_helpers as common

class RVExportMaterialInfo:
    def __init__(self, mat, is_world):
        self.alpha = 1.0
        self.is_env = not is_world
        self.env_color = (1,1,1,1)
        self.flags = 0
        self.texnum = common.get_texnum_from_material(mat)
        self.mul_vertex_color = False
        
        if mat is not None:
            if not mat.use_backface_culling:
                self.flags |= common.POLY_FLAG_DOUBLESIDED
            if mat.blend_method == 'HASHED' or mat.blend_method == 'BLEND':
                self.flags |= common.POLY_FLAG_TRANSLUCENT
            if mat.use_screen_refraction:
                self.flags |= common.POLY_FLAG_MIRROR
                
            if is_world and "anim_slot" in mat:
                anim_slot = mat["anim_slot"]
                if type(anim_slot) is int or type(anim_slot) is float:
                    anim_slot = int(anim_slot)
                    self.texnum = anim_slot
                    self.flags |= common.POLY_FLAG_ANIMATED

        add_node = common.get_material_node_of_type(mat, 'ADD_SHADER')
        if add_node is not None:
            # check if the add node is connected to the output
            # and has a transparent input. if those are true we can
            # guess it's an additive setup
            if (len(add_node.outputs[0].links) > 0 and add_node.outputs[0].links[0].to_node.type == 'OUTPUT_MATERIAL' and
                (len(add_node.inputs[0].links) > 0 and add_node.inputs[0].links[0].from_node.type == 'BSDF_TRANSPARENT' or
                 len(add_node.inputs[1].links) > 0 and add_node.inputs[1].links[0].from_node.type == 'BSDF_TRANSPARENT')):
                 self.flags |= common.POLY_FLAG_ADDITIVE
                
        
        principled = common.get_material_node_of_type(mat, 'BSDF_PRINCIPLED')
        if principled is not None:
            # env flag
            spec_input = principled.inputs["Specular"]
            spec_links = spec_input.links
            
            alpha_input = principled.inputs["Alpha"]
            alpha_links = alpha_input.links
            
            if len(alpha_links) > 0:
                if alpha_links[0].from_node.type == 'VERTEX_COLOR':
                    link = alpha_links[0]
                    self.mul_vertex_color = (link.from_socket.name == 'Alpha')
                elif alpha_links[0].from_node.type == 'MATH' and alpha_links[0].from_node.operation == 'MULTIPLY':
                    # check if vertex alpha is one of the inputs for math, and math mode is multiply
                    math_node = alpha_links[0].from_node
                    
                    self.mul_vertex_color = ((len(math_node.inputs[0].links) > 0 and math_node.inputs[0].links[0].from_node.type == 'VERTEX_COLOR' and math_node.inputs[0].links[0].from_socket.name == 'Alpha') or
                                             (len(math_node.inputs[1].links) > 0 and math_node.inputs[1].links[0].from_node.type == 'VERTEX_COLOR' and math_node.inputs[1].links[0].from_socket.name == 'Alpha'))
        
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

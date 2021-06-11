import bpy
import io_scene_revolt.common_helpers as common

class RV_FaceMaterialHash:
    def __init__(self, texnum, flags, is_world):
        # clear non-material related flags
        flags &= ~common.POLY_FLAG_QUAD
        
        # unset unsupported flags that will result in extra materials
        if is_world:
            flags &= ~common.POLY_FLAG_DISABLEENV
        else:
            flags &= ~common.POLY_FLAG_ENABLEENV
            flags &= ~common.POLY_FLAG_MIRROR

        # ----
        self.texnum = texnum
        self.flags = flags
        self.env_color = None
        self.has_env_color = False
        self.alpha = 1.0
        self.is_world = is_world
       
    def get_name(self):
        flags_str = ""
        if self.is_world and self.flags & common.POLY_FLAG_ENABLEENV:
            flags_str += "Env"
        elif not self.is_world and not self.flags & common.POLY_FLAG_DISABLEENV:
            flags_str += "Env"
        elif not self.is_world and self.flags & common.POLY_FLAG_DISABLEENV:
            flags_str += "NoEnv"
        
        if self.flags & common.POLY_FLAG_DOUBLESIDED:
            flags_str += "Double"
        if self.flags & common.POLY_FLAG_TRANSLUCENT:
            flags_str += "Translucent"
        if self.flags & common.POLY_FLAG_ADDITIVE:
            flags_str += "Add"
        if self.flags & common.POLY_FLAG_MIRROR:
            flags_str += "Mirror"
        
        name_str = "RVMaterial_"
        if self.texnum < 0:
            name_str += "NoTex"
        else:
            name_str += "Tex" + str(self.texnum)
            
        if len(flags_str) > 0:
            name_str += "_" + flags_str
        
        # DEBUG
        #name_str += "(" + str(self.flags) + ")"
        
        return name_str
        
    def make_material(self):
        mat = bpy.data.materials.new(name=self.get_name())

        mat.use_nodes = True
        mat.use_backface_culling = not (self.flags & common.POLY_FLAG_DOUBLESIDED)
        
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Roughness'].default_value = 0.05
        bsdf.inputs['Specular'].default_value = 0

        if self.has_env_color:
            # setup stuff
            rgb_node = mat.node_tree.nodes.new('ShaderNodeRGB')
            rgb_node.outputs[0].default_value = self.env_color
            
            mat.node_tree.links.new(bsdf.inputs['Specular'], rgb_node.outputs[0])
        else:
            if not self.is_world and not self.flags & common.POLY_FLAG_DISABLEENV:
                bsdf.inputs['Specular'].default_value = 0.05
            elif self.is_world and self.flags & common.POLY_FLAG_ENABLEENV:
                bsdf.inputs['Specular'].default_value = 0.05
        
        if self.flags & common.POLY_FLAG_TRANSLUCENT:
            bsdf.inputs['Alpha'].default_value = self.alpha
            mat.blend_method = 'BLEND'
            
        if self.flags & common.POLY_FLAG_MIRROR:
            bsdf.inputs['Specular'].default_value = 0.05
            mat.use_screen_refraction = True
            
        return mat

    def set_env_color(self, env_color):
        self.env_color = env_color
        self.has_env_color = True

    def set_alpha(self, alpha):
        self.alpha = alpha
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            env_equal = self.has_env_color == other.has_env_color
            if env_equal and self.has_env_color:
                for x in range(len(self.env_color)):
                    env_equal = (self.env_color[x] == other.env_color[x])
                    if not env_equal:
                        break
        
            return self.flags == other.flags and self.texnum == other.texnum and env_equal and self.alpha == other.alpha
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.texnum, self.flags, self.env_color, self.alpha))

# ReVoltBlenderAddon
A Blender addon I created because I wanted to work with Blender 2.9+, and the existing one wasn't compatible.

## What's Supported
Basic world (\*.w) exporting

Mesh (\*.w/\*.prm) exporting

## Installation (Windows)
Place the io_scene_revolt folder in the `%appdata%\Blender Foundation\Blender\2.90\scripts\addons` directory

## README: PORTING FROM OLD ADDON
The way you do flags etc has changed. The way I've written this is more of a WYSIWYG (what you see is what you get) approach.
- Texture number is based on the texture assigned to a material. Ex. if you assign "mytrack_a", it will export faces with this material as texture 0.
- Translucent flag is set by the "Blend Mode" on a material being either "Alpha Hashed" or "Alpha Blend"
  - Alpha value for vertex color is set by the "Alpha" slider in a "Principled BSDF" material 
- Env flag is set by the specularity of a "Principled BSDF" material. The higher this property, the more env.
- Double sided flag is set by a material having the "Backface Culling" option turned OFF
- Texture animations are currently not supported
- Mirror flag is currently not supported
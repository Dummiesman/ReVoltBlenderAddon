# ReVoltBlenderAddon
A Blender addon I created because I wanted to work with Blender 2.9+, and the existing one wasn't compatible.

## What's Supported
World (\*.w) export and import  
Mesh (\*.w/\*.prm) export and import  
Collision (\*.ncp) export and import  
Hull (\*.hul) export and import*  
Mirror Planes (\*.rim) export and import  

PSX Hull (\*.hul) import* 
PSX Mesh (\*.psm) import  
PSX World (\*.psw) import  

*\*this re-creates the hull based on it's vertices*

## Installation (Windows)
Place the io_scene_revolt folder in the `%appdata%\Blender Foundation\Blender\2.90\scripts\addons` directory

## README: WORKING WITH PRM/M/W
The way you do flags etc has changed. The way I've written this is more of a WYSIWYG (what you see is what you get) approach.
- Texture number is based on the texture assigned to a material. Ex. if you assign "mytrack_a", it will export faces with this material as texture 0.
- Translucent flag is set by the "Blend Mode" on a material being either "Alpha Hashed" or "Alpha Blend"
  - Alpha value for vertex color is set by the "Alpha" slider in a "Principled BSDF" material 
- Env flag is set by the specularity of a "Principled BSDF" material.
  - On tracks, hook up a Color node to the Specular input, this will be used as env color
  - On cars, just set the slider above 0 for env, or to 0 for no env
- Double sided flag is set by a material having the "Backface Culling" option turned OFF
- Texture animations are currently not supported
- Mirror flag is set by the "Screen Space Refraction" checkbox in material properties
- To setup an additive material, set it up as described on this page: https://b3d.interplanety.org/en/blender-eevee-transparency-blend-modes-multiply-and-additive/
- To use vertex alpha, add a "Vertex Color" node to the material, and connect the alpha output to the alpha input of the principled setup

**The W exporter also functions as an alternative to WorldCut!** Just select the "Split Meshes" option upon exporting.

## README: WORKING WITH NCP
The way collision is setup has changed.
- Select your collision object, open the search menu, and locate "Setup NCP Object"
  - This will add NCP materials to the objects material list
- Camera only / Object only flags are done with Face Maps, these are in the "Mesh Data" tab of the object

## README: WORKING WITH HUL
- Selected objects will be exported as convex hulls
- Any object named "HullSphere" is exported as a sphere
  - The size of exported spheres is the average *scale* of the object. To make a 'compatible' sphere model, create a 1 diameter UV sphere.

## README: WORKING WITH RIM
- Any object named "MirrorPlane" is exported as mirror planes
  - Using "Selected Only" will override this behavior

## KNOWN ISSUES
- PSX import may have incorrectly created materials
- PSX stores double sided polygons as individual polygons, and Blender doesn't like 2 polygons sharing vertices. So these don't import currently.

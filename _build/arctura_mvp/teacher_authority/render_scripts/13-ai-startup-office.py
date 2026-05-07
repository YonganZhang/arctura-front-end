#!/usr/bin/env python3
"""Auto-generated Blender Python script from blender-cli."""

import bpy
import math
import os

# ── Clear Default Scene ──────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ── Scene Settings ──────────────────────────────────────────
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.frame_start = 1
scene.frame_end = 250
scene.frame_current = 1
scene.render.fps = 24

# ── Render Settings ─────────────────────────────────────────
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.eevee.taa_render_samples = 64

# ── World Settings ──────────────────────────────────────────
world = bpy.data.worlds.get('World')
if world is None:
    world = bpy.data.worlds.new('World')
    scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get('Background')
if bg_node:
    bg_node.inputs[0].default_value = (0.05, 0.05, 0.05, 1.0)

# ── Materials ───────────────────────────────────────────────
mat_Concrete = bpy.data.materials.new(name='Concrete')
mat_Concrete.use_nodes = True
bsdf_Concrete = mat_Concrete.node_tree.nodes.get('Principled BSDF')
if bsdf_Concrete:
    bsdf_Concrete.inputs['Base Color'].default_value = (0.71, 0.69, 0.66, 1.0)
    bsdf_Concrete.inputs['Metallic'].default_value = 0.05
    bsdf_Concrete.inputs['Roughness'].default_value = 0.7
    bsdf_Concrete.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Concrete.inputs['Alpha'].default_value = 1.0

mat_WarmWood = bpy.data.materials.new(name='WarmWood')
mat_WarmWood.use_nodes = True
bsdf_WarmWood = mat_WarmWood.node_tree.nodes.get('Principled BSDF')
if bsdf_WarmWood:
    bsdf_WarmWood.inputs['Base Color'].default_value = (0.55, 0.42, 0.3, 1.0)
    bsdf_WarmWood.inputs['Metallic'].default_value = 0.0
    bsdf_WarmWood.inputs['Roughness'].default_value = 0.5
    bsdf_WarmWood.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WarmWood.inputs['Alpha'].default_value = 1.0

mat_DeepTeal = bpy.data.materials.new(name='DeepTeal')
mat_DeepTeal.use_nodes = True
bsdf_DeepTeal = mat_DeepTeal.node_tree.nodes.get('Principled BSDF')
if bsdf_DeepTeal:
    bsdf_DeepTeal.inputs['Base Color'].default_value = (0.18, 0.33, 0.33, 1.0)
    bsdf_DeepTeal.inputs['Metallic'].default_value = 0.2
    bsdf_DeepTeal.inputs['Roughness'].default_value = 0.5
    bsdf_DeepTeal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_DeepTeal.inputs['Alpha'].default_value = 1.0

mat_SoftWhite = bpy.data.materials.new(name='SoftWhite')
mat_SoftWhite.use_nodes = True
bsdf_SoftWhite = mat_SoftWhite.node_tree.nodes.get('Principled BSDF')
if bsdf_SoftWhite:
    bsdf_SoftWhite.inputs['Base Color'].default_value = (0.94, 0.93, 0.89, 1.0)
    bsdf_SoftWhite.inputs['Metallic'].default_value = 0.0
    bsdf_SoftWhite.inputs['Roughness'].default_value = 0.85
    bsdf_SoftWhite.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_SoftWhite.inputs['Alpha'].default_value = 1.0

mat_LimeGreen = bpy.data.materials.new(name='LimeGreen')
mat_LimeGreen.use_nodes = True
bsdf_LimeGreen = mat_LimeGreen.node_tree.nodes.get('Principled BSDF')
if bsdf_LimeGreen:
    bsdf_LimeGreen.inputs['Base Color'].default_value = (0.66, 0.79, 0.28, 1.0)
    bsdf_LimeGreen.inputs['Metallic'].default_value = 0.1
    bsdf_LimeGreen.inputs['Roughness'].default_value = 0.6
    bsdf_LimeGreen.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_LimeGreen.inputs['Alpha'].default_value = 1.0

mat_Charcoal = bpy.data.materials.new(name='Charcoal')
mat_Charcoal.use_nodes = True
bsdf_Charcoal = mat_Charcoal.node_tree.nodes.get('Principled BSDF')
if bsdf_Charcoal:
    bsdf_Charcoal.inputs['Base Color'].default_value = (0.16, 0.16, 0.17, 1.0)
    bsdf_Charcoal.inputs['Metallic'].default_value = 0.3
    bsdf_Charcoal.inputs['Roughness'].default_value = 0.45
    bsdf_Charcoal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Charcoal.inputs['Alpha'].default_value = 1.0

mat_Glass = bpy.data.materials.new(name='Glass')
mat_Glass.use_nodes = True
bsdf_Glass = mat_Glass.node_tree.nodes.get('Principled BSDF')
if bsdf_Glass:
    bsdf_Glass.inputs['Base Color'].default_value = (0.82, 0.9, 0.95, 1.0)
    bsdf_Glass.inputs['Metallic'].default_value = 0.2
    bsdf_Glass.inputs['Roughness'].default_value = 0.05
    bsdf_Glass.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Glass.inputs['Alpha'].default_value = 1.0

mat_ScreenDark = bpy.data.materials.new(name='ScreenDark')
mat_ScreenDark.use_nodes = True
bsdf_ScreenDark = mat_ScreenDark.node_tree.nodes.get('Principled BSDF')
if bsdf_ScreenDark:
    bsdf_ScreenDark.inputs['Base Color'].default_value = (0.05, 0.06, 0.1, 1.0)
    bsdf_ScreenDark.inputs['Metallic'].default_value = 0.1
    bsdf_ScreenDark.inputs['Roughness'].default_value = 0.2
    bsdf_ScreenDark.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_ScreenDark.inputs['Alpha'].default_value = 1.0

mat_LED_Blue = bpy.data.materials.new(name='LED_Blue')
mat_LED_Blue.use_nodes = True
bsdf_LED_Blue = mat_LED_Blue.node_tree.nodes.get('Principled BSDF')
if bsdf_LED_Blue:
    bsdf_LED_Blue.inputs['Base Color'].default_value = (0.15, 0.55, 0.95, 1.0)
    bsdf_LED_Blue.inputs['Metallic'].default_value = 0.7
    bsdf_LED_Blue.inputs['Roughness'].default_value = 0.15
    bsdf_LED_Blue.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_LED_Blue.inputs['Alpha'].default_value = 1.0

mat_Foliage = bpy.data.materials.new(name='Foliage')
mat_Foliage.use_nodes = True
bsdf_Foliage = mat_Foliage.node_tree.nodes.get('Principled BSDF')
if bsdf_Foliage:
    bsdf_Foliage.inputs['Base Color'].default_value = (0.22, 0.5, 0.26, 1.0)
    bsdf_Foliage.inputs['Metallic'].default_value = 0.0
    bsdf_Foliage.inputs['Roughness'].default_value = 0.85
    bsdf_Foliage.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Foliage.inputs['Alpha'].default_value = 1.0

mat_Terracotta = bpy.data.materials.new(name='Terracotta')
mat_Terracotta.use_nodes = True
bsdf_Terracotta = mat_Terracotta.node_tree.nodes.get('Principled BSDF')
if bsdf_Terracotta:
    bsdf_Terracotta.inputs['Base Color'].default_value = (0.6, 0.35, 0.25, 1.0)
    bsdf_Terracotta.inputs['Metallic'].default_value = 0.0
    bsdf_Terracotta.inputs['Roughness'].default_value = 0.7
    bsdf_Terracotta.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Terracotta.inputs['Alpha'].default_value = 1.0

mat_Steel = bpy.data.materials.new(name='Steel')
mat_Steel.use_nodes = True
bsdf_Steel = mat_Steel.node_tree.nodes.get('Principled BSDF')
if bsdf_Steel:
    bsdf_Steel.inputs['Base Color'].default_value = (0.7, 0.72, 0.75, 1.0)
    bsdf_Steel.inputs['Metallic'].default_value = 0.92
    bsdf_Steel.inputs['Roughness'].default_value = 0.3
    bsdf_Steel.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Steel.inputs['Alpha'].default_value = 1.0

mat_LogoAccent = bpy.data.materials.new(name='LogoAccent')
mat_LogoAccent.use_nodes = True
bsdf_LogoAccent = mat_LogoAccent.node_tree.nodes.get('Principled BSDF')
if bsdf_LogoAccent:
    bsdf_LogoAccent.inputs['Base Color'].default_value = (0.66, 0.79, 0.28, 1.0)
    bsdf_LogoAccent.inputs['Metallic'].default_value = 0.4
    bsdf_LogoAccent.inputs['Roughness'].default_value = 0.3
    bsdf_LogoAccent.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_LogoAccent.inputs['Alpha'].default_value = 1.0

mat_Whiteboard = bpy.data.materials.new(name='Whiteboard')
mat_Whiteboard.use_nodes = True
bsdf_Whiteboard = mat_Whiteboard.node_tree.nodes.get('Principled BSDF')
if bsdf_Whiteboard:
    bsdf_Whiteboard.inputs['Base Color'].default_value = (0.97, 0.97, 0.95, 1.0)
    bsdf_Whiteboard.inputs['Metallic'].default_value = 0.05
    bsdf_Whiteboard.inputs['Roughness'].default_value = 0.2
    bsdf_Whiteboard.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Whiteboard.inputs['Alpha'].default_value = 1.0


# ── Objects ─────────────────────────────────────────────────
# Object: Floor
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, 0.0, 0.0))
obj = bpy.context.active_object
obj.name = 'Floor'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (6.5, 5.0, 1.0)
if 'mat_Concrete' in dir():
    obj.data.materials.append(mat_Concrete)

# Object: WallN
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 5.0, 1.5))
obj = bpy.context.active_object
obj.name = 'WallN'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (6.5, 0.05, 1.5)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: WallS
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, -5.0, 1.5))
obj = bpy.context.active_object
obj.name = 'WallS'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (6.5, 0.05, 1.5)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: WallW
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-6.5, 0.0, 1.5))
obj = bpy.context.active_object
obj.name = 'WallW'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 5.0, 1.5)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: WallE
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(6.5, 0.0, 1.5))
obj = bpy.context.active_object
obj.name = 'WallE'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 5.0, 1.5)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: Ceiling
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, 0.0, 3.0))
obj = bpy.context.active_object
obj.name = 'Ceiling'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (6.5, 5.0, 1.0)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: LogoPanel
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.5, -4.9, 1.8))
obj = bpy.context.active_object
obj.name = 'LogoPanel'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.5, 0.05, 0.8)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: LogoAccentBar
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.5, -4.85, 1.8))
obj = bpy.context.active_object
obj.name = 'LogoAccentBar'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.3, 0.04, 0.08)
if 'mat_LimeGreen' in dir():
    obj.data.materials.append(mat_LimeGreen)

# Object: ReceptionDesk
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, -3.7, 0.55))
obj = bpy.context.active_object
obj.name = 'ReceptionDesk'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.0, 0.5, 0.55)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: WaitBench
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.5, -3.5, 0.25))
obj = bpy.context.active_object
obj.name = 'WaitBench'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.3, 0.25)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: EntryMat
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.5, -4.3, 0.01))
obj = bpy.context.active_object
obj.name = 'EntryMat'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.7, 0.4, 0.01)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: Desk_r-1.5_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r-1.5_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r-1.5_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, -2.1, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r-1.5_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r-1.5_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.2, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r-1.5_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r-1.5_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.8, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r-1.5_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r-1.5_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.6, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r-1.5_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r-1.5_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.6, -2.1, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r-1.5_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r-1.5_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.8000000000000003, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r-1.5_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r-1.5_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.4, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r-1.5_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r-1.5_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.2, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r-1.5_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r-1.5_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.2, -2.1, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r-1.5_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r-1.5_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.4000000000000004, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r-1.5_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r-1.5_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r-1.5_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r-1.5_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.8000000000000007, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r-1.5_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r-1.5_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.8000000000000007, -2.1, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r-1.5_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r-1.5_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.0000000000000007, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r-1.5_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r-1.5_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.6000000000000008, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r-1.5_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r-1.5_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.5999999999999996, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r-1.5_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r-1.5_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.5999999999999996, -2.1, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r-1.5_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r-1.5_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.39999999999999963, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r-1.5_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r-1.5_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.7999999999999996, -1.5, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r-1.5_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r1.8_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, 1.8, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r1.8_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r1.8_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, 2.4, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r1.8_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r1.8_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.2, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r1.8_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r1.8_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.8, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r1.8_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r1.8_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.6, 1.8, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r1.8_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r1.8_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.6, 2.4, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r1.8_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r1.8_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.8000000000000003, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r1.8_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r1.8_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.4, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r1.8_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r1.8_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.2, 1.8, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r1.8_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r1.8_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.2, 2.4, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r1.8_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r1.8_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.4000000000000004, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r1.8_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r1.8_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r1.8_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r1.8_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.8000000000000007, 1.8, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r1.8_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r1.8_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.8000000000000007, 2.4, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r1.8_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r1.8_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.0000000000000007, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r1.8_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r1.8_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.6000000000000008, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r1.8_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: Desk_r1.8_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.5999999999999996, 1.8, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk_r1.8_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Chair_r1.8_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.5999999999999996, 2.4, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair_r1.8_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ScrL_r1.8_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.39999999999999963, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrL_r1.8_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: ScrR_r1.8_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.7999999999999996, 1.8, 1.15))
obj = bpy.context.active_object
obj.name = 'ScrR_r1.8_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.02, 0.16)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: DeskDivider
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 0.15, 1.1))
obj = bpy.context.active_object
obj.name = 'DeskDivider'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (4.3, 0.02, 0.35)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: GPU_GlassW
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.0, 3.5, 1.5))
obj = bpy.context.active_object
obj.name = 'GPU_GlassW'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.03, 1.5, 1.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: GPU_GlassS
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.75, 2.0, 1.5))
obj = bpy.context.active_object
obj.name = 'GPU_GlassS'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.75, 0.03, 1.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: GPU_Door
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.03, 2.0, 1.05))
obj = bpy.context.active_object
obj.name = 'GPU_Door'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.35, 1.05)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: Rack1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.8, 3.8, 1.0))
obj = bpy.context.active_object
obj.name = 'Rack1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.5, 1.0)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: Rack2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.8, 3.8, 1.0))
obj = bpy.context.active_object
obj.name = 'Rack2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.5, 1.0)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: Rack3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.8, 3.8, 1.0))
obj = bpy.context.active_object
obj.name = 'Rack3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.5, 1.0)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: LED1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.8, 3.8, 2.02))
obj = bpy.context.active_object
obj.name = 'LED1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.28, 0.48, 0.02)
if 'mat_LED_Blue' in dir():
    obj.data.materials.append(mat_LED_Blue)

# Object: LED2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.8, 3.8, 2.02))
obj = bpy.context.active_object
obj.name = 'LED2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.28, 0.48, 0.02)
if 'mat_LED_Blue' in dir():
    obj.data.materials.append(mat_LED_Blue)

# Object: LED3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.8, 3.8, 2.02))
obj = bpy.context.active_object
obj.name = 'LED3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.28, 0.48, 0.02)
if 'mat_LED_Blue' in dir():
    obj.data.materials.append(mat_LED_Blue)

# Object: LEDstrip
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.05, 2.5, 1.5))
obj = bpy.context.active_object
obj.name = 'LEDstrip'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.02, 1.3)
if 'mat_LED_Blue' in dir():
    obj.data.materials.append(mat_LED_Blue)

# Object: MR_GlassW
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.0, -3.0, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_GlassW'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.03, 2.0, 1.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: MR_GlassN
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.25, -1.0, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_GlassN'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.25, 0.03, 1.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: MR_FrameE
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(6.47, -3.0, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_FrameE'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 2.0, 1.5)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_FrameS
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.25, -4.97, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_FrameS'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.25, 0.02, 1.5)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_Door
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.03, -1.5, 1.05))
obj = bpy.context.active_object
obj.name = 'MR_Door'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.45, 1.05)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: MR_Table
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.25, -3.0, 0.73))
obj = bpy.context.active_object
obj.name = 'MR_Table'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.2, 0.5, 0.03)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: MR_ChairN_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.2, -4.2, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairN_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairS_0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.3, -4.2, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairS_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairN_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.2, -3.6, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairN_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairS_1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.3, -3.6, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairS_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairN_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.2, -3.0, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairN_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairS_2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.3, -3.0, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairS_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairN_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.2, -2.4000000000000004, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairN_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairS_3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.3, -2.4000000000000004, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairS_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairN_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.2, -1.8000000000000003, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairN_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_ChairS_4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.3, -1.8000000000000003, 0.43))
obj = bpy.context.active_object
obj.name = 'MR_ChairS_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.22, 0.22, 0.03)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: MR_BigScreen
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(6.4, -3.0, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_BigScreen'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.7, 0.45)
if 'mat_ScreenDark' in dir():
    obj.data.materials.append(mat_ScreenDark)

# Object: MR_Whiteboard
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.25, -4.93, 1.5))
obj = bpy.context.active_object
obj.name = 'MR_Whiteboard'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.9, 0.015, 0.8)
if 'mat_Whiteboard' in dir():
    obj.data.materials.append(mat_Whiteboard)

# Object: PhoneBooth1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.5, 0.0, 1.25))
obj = bpy.context.active_object
obj.name = 'PhoneBooth1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.6, 1.25)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: Booth1_Door
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.89, 0.0, 1.1))
obj = bpy.context.active_object
obj.name = 'Booth1_Door'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.35, 1.1)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: Booth1_Desk
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.5, 0.3, 0.75))
obj = bpy.context.active_object
obj.name = 'Booth1_Desk'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: PhoneBooth2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.5, 1.5, 1.25))
obj = bpy.context.active_object
obj.name = 'PhoneBooth2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.6, 1.25)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: Booth2_Door
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.89, 1.5, 1.1))
obj = bpy.context.active_object
obj.name = 'Booth2_Door'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.35, 1.1)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: Booth2_Desk
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.5, 1.2, 0.75))
obj = bpy.context.active_object
obj.name = 'Booth2_Desk'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: KitCounter
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.5, 4.5, 0.45))
obj = bpy.context.active_object
obj.name = 'KitCounter'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.0, 0.35, 0.45)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: KitSink
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.9, 4.5, 0.92))
obj = bpy.context.active_object
obj.name = 'KitSink'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.15, 0.02)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: KitFridge
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-6.2, 4.5, 0.85))
obj = bpy.context.active_object
obj.name = 'KitFridge'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.3, 0.85)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: KitCoffee
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.3, 4.5, 1.05))
obj = bpy.context.active_object
obj.name = 'KitCoffee'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.15)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: KitMicro
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.8, 4.5, 1.0))
obj = bpy.context.active_object
obj.name = 'KitMicro'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.18, 0.12)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: KitUpCab
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.5, 4.9, 2.3))
obj = bpy.context.active_object
obj.name = 'KitUpCab'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.0, 0.12, 0.35)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Sofa1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.5, -2.0, 0.35))
obj = bpy.context.active_object
obj.name = 'Sofa1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.35, 0.35)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: Sofa2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.3, -2.0, 0.35))
obj = bpy.context.active_object
obj.name = 'Sofa2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.35, 0.35)
if 'mat_DeepTeal' in dir():
    obj.data.materials.append(mat_DeepTeal)

# Object: CoffeeTable
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.4, -2.8, 0.25))
obj = bpy.context.active_object
obj.name = 'CoffeeTable'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.25, 0.03)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Foosball
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.4, -0.8, 0.55))
obj = bpy.context.active_object
obj.name = 'Foosball'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.7, 0.35, 0.1)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: Foosball_leg1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.8, -0.8, 0.225))
obj = bpy.context.active_object
obj.name = 'Foosball_leg1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.04, 0.04, 0.225)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: Foosball_leg2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.0, -0.8, 0.225))
obj = bpy.context.active_object
obj.name = 'Foosball_leg2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.04, 0.04, 0.225)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: BeanBag1
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-0.3, -2.8, 0.3))
obj = bpy.context.active_object
obj.name = 'BeanBag1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.3, 0.3)
if 'mat_LimeGreen' in dir():
    obj.data.materials.append(mat_LimeGreen)

# Object: BeanBag2
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(2.9, -2.5, 0.3))
obj = bpy.context.active_object
obj.name = 'BeanBag2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.3, 0.3)
if 'mat_LimeGreen' in dir():
    obj.data.materials.append(mat_LimeGreen)

# Object: BathWall1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, -0.5, 1.2))
obj = bpy.context.active_object
obj.name = 'BathWall1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.8, 1.2)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: BathWall2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.75, 0.3, 1.2))
obj = bpy.context.active_object
obj.name = 'BathWall2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.75, 0.02, 1.2)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: Toilet
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-6.2, -0.3, 0.25))
obj = bpy.context.active_object
obj.name = 'Toilet'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.25)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: BathSink
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-6.2, 0.1, 0.5))
obj = bpy.context.active_object
obj.name = 'BathSink'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.15, 0.05)
if 'mat_SoftWhite' in dir():
    obj.data.materials.append(mat_SoftWhite)

# Object: PlantPot_0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-6.0, -2.5, 0.3))
obj = bpy.context.active_object
obj.name = 'PlantPot_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: PlantFoliage_0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-6.0, -2.5, 1.0))
obj = bpy.context.active_object
obj.name = 'PlantFoliage_0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.5)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: PlantPot_1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-6.0, 2.5, 0.3))
obj = bpy.context.active_object
obj.name = 'PlantPot_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: PlantFoliage_1
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-6.0, 2.5, 1.0))
obj = bpy.context.active_object
obj.name = 'PlantFoliage_1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.5)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: PlantPot_2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(6.0, -2.5, 0.3))
obj = bpy.context.active_object
obj.name = 'PlantPot_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: PlantFoliage_2
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(6.0, -2.5, 1.0))
obj = bpy.context.active_object
obj.name = 'PlantFoliage_2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.5)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: PlantPot_3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.0, 4.5, 0.3))
obj = bpy.context.active_object
obj.name = 'PlantPot_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: PlantFoliage_3
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(0.0, 4.5, 1.0))
obj = bpy.context.active_object
obj.name = 'PlantFoliage_3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.5)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: PlantPot_4
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-0.5, -4.0, 0.3))
obj = bpy.context.active_object
obj.name = 'PlantPot_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: PlantFoliage_4
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-0.5, -4.0, 1.0))
obj = bpy.context.active_object
obj.name = 'PlantFoliage_4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.5)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: CeilTrack1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.0, 0.2, 2.95))
obj = bpy.context.active_object
obj.name = 'CeilTrack1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (3.0, 0.05, 0.02)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: CeilTrack2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.0, 0.2, 2.95))
obj = bpy.context.active_object
obj.name = 'CeilTrack2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (3.0, 0.05, 0.02)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: Pendant1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.4, -2.0, 2.5))
obj = bpy.context.active_object
obj.name = 'Pendant1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.08, 0.08, 0.15)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)

# Object: Pendant2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.25, -3.0, 2.4))
obj = bpy.context.active_object
obj.name = 'Pendant2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.15)
if 'mat_Steel' in dir():
    obj.data.materials.append(mat_Steel)


# ── Cameras ─────────────────────────────────────────────────
cam_data = bpy.data.cameras.new(name='Camera')
cam_data.type = 'PERSP'
cam_data.lens = 20.0
cam_data.sensor_width = 36.0
cam_data.clip_start = 0.1
cam_data.clip_end = 1000.0
cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (-7.5, -8.0, 4.2)
cam_obj.rotation_euler = (math.radians(70.0), math.radians(0.0), math.radians(-35.0))
scene.camera = cam_obj


# ── Lights ──────────────────────────────────────────────────
light_data = bpy.data.lights.new(name='Sun', type='SUN')
light_data.energy = 4.0
light_data.color = (1.0, 0.97, 0.9)
light_data.angle = 0.00918
light_obj = bpy.data.objects.new('Sun', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (10.0, -10.0, 8.0)
light_obj.rotation_euler = (math.radians(60.0), math.radians(0.0), math.radians(-45.0))

light_data = bpy.data.lights.new(name='Area', type='AREA')
light_data.energy = 200.0
light_data.color = (1.0, 0.95, 0.85)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (-3.0, 0.5, 2.9)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Area.001', type='AREA')
light_data.energy = 200.0
light_data.color = (1.0, 0.95, 0.85)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area.001', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (3.0, 0.5, 2.9)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Point', type='POINT')
light_data.energy = 50.0
light_data.color = (0.3, 0.6, 1.0)
light_data.shadow_soft_size = 0.25
light_obj = bpy.data.objects.new('Point', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (4.8, 3.8, 2.0)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Point.001', type='POINT')
light_data.energy = 40.0
light_data.color = (0.8, 0.95, 0.4)
light_data.shadow_soft_size = 0.25
light_obj = bpy.data.objects.new('Point.001', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (-4.5, -4.5, 2.5)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))


# ── Keyframes ───────────────────────────────────────────────
# (none)

# ── Render Output ───────────────────────────────────────────
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = r'/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office/render.png'
scene.frame_set(1)

# Render single frame
bpy.ops.render.render(write_still=True)

print('Render complete: /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office/render.png')
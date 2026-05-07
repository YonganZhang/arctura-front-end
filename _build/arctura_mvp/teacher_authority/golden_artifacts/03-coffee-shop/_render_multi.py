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
mat_TerrazzoFloor = bpy.data.materials.new(name='TerrazzoFloor')
mat_TerrazzoFloor.use_nodes = True
bsdf_TerrazzoFloor = mat_TerrazzoFloor.node_tree.nodes.get('Principled BSDF')
if bsdf_TerrazzoFloor:
    bsdf_TerrazzoFloor.inputs['Base Color'].default_value = (0.8, 0.78, 0.72, 1.0)
    bsdf_TerrazzoFloor.inputs['Metallic'].default_value = 0.05
    bsdf_TerrazzoFloor.inputs['Roughness'].default_value = 0.35
    bsdf_TerrazzoFloor.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_TerrazzoFloor.inputs['Alpha'].default_value = 1.0

mat_CreamWall = bpy.data.materials.new(name='CreamWall')
mat_CreamWall.use_nodes = True
bsdf_CreamWall = mat_CreamWall.node_tree.nodes.get('Principled BSDF')
if bsdf_CreamWall:
    bsdf_CreamWall.inputs['Base Color'].default_value = (0.92, 0.9, 0.85, 1.0)
    bsdf_CreamWall.inputs['Metallic'].default_value = 0.0
    bsdf_CreamWall.inputs['Roughness'].default_value = 0.92
    bsdf_CreamWall.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_CreamWall.inputs['Alpha'].default_value = 1.0

mat_WarmWood = bpy.data.materials.new(name='WarmWood')
mat_WarmWood.use_nodes = True
bsdf_WarmWood = mat_WarmWood.node_tree.nodes.get('Principled BSDF')
if bsdf_WarmWood:
    bsdf_WarmWood.inputs['Base Color'].default_value = (0.55, 0.42, 0.3, 1.0)
    bsdf_WarmWood.inputs['Metallic'].default_value = 0.0
    bsdf_WarmWood.inputs['Roughness'].default_value = 0.5
    bsdf_WarmWood.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WarmWood.inputs['Alpha'].default_value = 1.0

mat_BlackMetal = bpy.data.materials.new(name='BlackMetal')
mat_BlackMetal.use_nodes = True
bsdf_BlackMetal = mat_BlackMetal.node_tree.nodes.get('Principled BSDF')
if bsdf_BlackMetal:
    bsdf_BlackMetal.inputs['Base Color'].default_value = (0.15, 0.15, 0.17, 1.0)
    bsdf_BlackMetal.inputs['Metallic'].default_value = 0.85
    bsdf_BlackMetal.inputs['Roughness'].default_value = 0.35
    bsdf_BlackMetal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_BlackMetal.inputs['Alpha'].default_value = 1.0

mat_Brass = bpy.data.materials.new(name='Brass')
mat_Brass.use_nodes = True
bsdf_Brass = mat_Brass.node_tree.nodes.get('Principled BSDF')
if bsdf_Brass:
    bsdf_Brass.inputs['Base Color'].default_value = (0.72, 0.6, 0.35, 1.0)
    bsdf_Brass.inputs['Metallic'].default_value = 0.95
    bsdf_Brass.inputs['Roughness'].default_value = 0.25
    bsdf_Brass.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Brass.inputs['Alpha'].default_value = 1.0

mat_Foliage = bpy.data.materials.new(name='Foliage')
mat_Foliage.use_nodes = True
bsdf_Foliage = mat_Foliage.node_tree.nodes.get('Principled BSDF')
if bsdf_Foliage:
    bsdf_Foliage.inputs['Base Color'].default_value = (0.25, 0.48, 0.25, 1.0)
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

mat_PendantCream = bpy.data.materials.new(name='PendantCream')
mat_PendantCream.use_nodes = True
bsdf_PendantCream = mat_PendantCream.node_tree.nodes.get('Principled BSDF')
if bsdf_PendantCream:
    bsdf_PendantCream.inputs['Base Color'].default_value = (0.95, 0.88, 0.7, 1.0)
    bsdf_PendantCream.inputs['Metallic'].default_value = 0.2
    bsdf_PendantCream.inputs['Roughness'].default_value = 0.5
    bsdf_PendantCream.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_PendantCream.inputs['Alpha'].default_value = 1.0

mat_GlassCase = bpy.data.materials.new(name='GlassCase')
mat_GlassCase.use_nodes = True
bsdf_GlassCase = mat_GlassCase.node_tree.nodes.get('Principled BSDF')
if bsdf_GlassCase:
    bsdf_GlassCase.inputs['Base Color'].default_value = (0.9, 0.92, 0.95, 1.0)
    bsdf_GlassCase.inputs['Metallic'].default_value = 0.3
    bsdf_GlassCase.inputs['Roughness'].default_value = 0.05
    bsdf_GlassCase.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_GlassCase.inputs['Alpha'].default_value = 1.0

mat_BookDark = bpy.data.materials.new(name='BookDark')
mat_BookDark.use_nodes = True
bsdf_BookDark = mat_BookDark.node_tree.nodes.get('Principled BSDF')
if bsdf_BookDark:
    bsdf_BookDark.inputs['Base Color'].default_value = (0.35, 0.25, 0.2, 1.0)
    bsdf_BookDark.inputs['Metallic'].default_value = 0.1
    bsdf_BookDark.inputs['Roughness'].default_value = 0.75
    bsdf_BookDark.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_BookDark.inputs['Alpha'].default_value = 1.0

mat_StainlessSteel = bpy.data.materials.new(name='StainlessSteel')
mat_StainlessSteel.use_nodes = True
bsdf_StainlessSteel = mat_StainlessSteel.node_tree.nodes.get('Principled BSDF')
if bsdf_StainlessSteel:
    bsdf_StainlessSteel.inputs['Base Color'].default_value = (0.7, 0.72, 0.75, 1.0)
    bsdf_StainlessSteel.inputs['Metallic'].default_value = 0.92
    bsdf_StainlessSteel.inputs['Roughness'].default_value = 0.3
    bsdf_StainlessSteel.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_StainlessSteel.inputs['Alpha'].default_value = 1.0

mat_Cord = bpy.data.materials.new(name='Cord')
mat_Cord.use_nodes = True
bsdf_Cord = mat_Cord.node_tree.nodes.get('Principled BSDF')
if bsdf_Cord:
    bsdf_Cord.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
    bsdf_Cord.inputs['Metallic'].default_value = 0.0
    bsdf_Cord.inputs['Roughness'].default_value = 0.8
    bsdf_Cord.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Cord.inputs['Alpha'].default_value = 1.0


# ── Objects ─────────────────────────────────────────────────
# Object: Floor
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, 0.0, 0.0))
obj = bpy.context.active_object
obj.name = 'Floor'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (5.0, 4.0, 1.0)
if 'mat_TerrazzoFloor' in dir():
    obj.data.materials.append(mat_TerrazzoFloor)

# Object: WallBack
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 4.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallBack'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (5.0, 0.05, 1.75)
if 'mat_CreamWall' in dir():
    obj.data.materials.append(mat_CreamWall)

# Object: WallFront
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, -4.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallFront'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (5.0, 0.05, 1.75)
if 'mat_CreamWall' in dir():
    obj.data.materials.append(mat_CreamWall)

# Object: WallLeft
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, 0.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallLeft'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 4.0, 1.75)
if 'mat_CreamWall' in dir():
    obj.data.materials.append(mat_CreamWall)

# Object: WallRight
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.0, 0.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallRight'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 4.0, 1.75)
if 'mat_CreamWall' in dir():
    obj.data.materials.append(mat_CreamWall)

# Object: WallKitchen
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.5, 2.0, 1.3))
obj = bpy.context.active_object
obj.name = 'WallKitchen'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 2.0, 1.3)
if 'mat_CreamWall' in dir():
    obj.data.materials.append(mat_CreamWall)

# Object: BarH
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 2.5, 0.55))
obj = bpy.context.active_object
obj.name = 'BarH'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.2, 0.5, 0.55)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BarV
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.2, 1.5, 0.55))
obj = bpy.context.active_object
obj.name = 'BarV'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 1.1, 0.55)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BackBar
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 3.85, 1.75))
obj = bpy.context.active_object
obj.name = 'BackBar'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.2, 0.1, 1.6)
if 'mat_BookDark' in dir():
    obj.data.materials.append(mat_BookDark)

# Object: Shelf0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 3.75, 0.7))
obj = bpy.context.active_object
obj.name = 'Shelf0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.18, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Shelf1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 3.75, 1.25))
obj = bpy.context.active_object
obj.name = 'Shelf1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.18, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Shelf2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, 3.75, 1.8))
obj = bpy.context.active_object
obj.name = 'Shelf2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.18, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: EspressoMachine
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.5, 2.4, 1.35))
obj = bpy.context.active_object
obj.name = 'EspressoMachine'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.3, 0.25)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: DisplayCase
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.8, 2.4, 1.3))
obj = bpy.context.active_object
obj.name = 'DisplayCase'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.25, 0.2)
if 'mat_GlassCase' in dir():
    obj.data.materials.append(mat_GlassCase)

# Object: SmallTable0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'SmallTable0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: TableStem0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -2.5, 0.375))
obj = bpy.context.active_object
obj.name = 'TableStem0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.07, 0.07, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ChairA0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.75, -2.5, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairA0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairAB0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.75, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairAB0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairB0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.65, -2.5, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairB0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairBB0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.65, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairBB0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: SmallTable1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'SmallTable1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: TableStem1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -2.5, 0.375))
obj = bpy.context.active_object
obj.name = 'TableStem1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.07, 0.07, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ChairA1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.05, -2.5, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairA1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairAB1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.05, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairAB1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairB1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.95, -2.5, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairB1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairBB1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.95, -2.5, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairBB1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: SmallTable2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'SmallTable2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: TableStem2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -1.0, 0.375))
obj = bpy.context.active_object
obj.name = 'TableStem2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.07, 0.07, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ChairA2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.75, -1.0, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairA2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairAB2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.75, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairAB2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairB2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.65, -1.0, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairB2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairBB2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.65, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairBB2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: SmallTable3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'SmallTable3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: TableStem3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -1.0, 0.375))
obj = bpy.context.active_object
obj.name = 'TableStem3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.07, 0.07, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ChairA3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.05, -1.0, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairA3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairAB3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.05, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairAB3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairB3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.95, -1.0, 0.45))
obj = bpy.context.active_object
obj.name = 'ChairB3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ChairBB3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.95, -1.0, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairBB3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.04, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: LongTable
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.0, -1.5, 0.75))
obj = bpy.context.active_object
obj.name = 'LongTable'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.6, 0.45, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: LongLegA
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.45, -1.5, 0.375))
obj = bpy.context.active_object
obj.name = 'LongLegA'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.04, 0.04, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: LongLegB
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.55, -1.5, 0.375))
obj = bpy.context.active_object
obj.name = 'LongLegB'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.04, 0.04, 0.375)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: StoolN0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.75, -0.95, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolN0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolS0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.75, -2.05, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolS0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolN1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.45, -0.95, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolN1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolS1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.45, -2.05, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolS1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolN2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.15, -0.95, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolN2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolS2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.15, -2.05, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolS2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolN3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.85, -0.95, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolN3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: StoolS3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.85, -2.05, 0.45))
obj = bpy.context.active_object
obj.name = 'StoolS3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.025)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BookWall
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.85, -1.0, 1.75))
obj = bpy.context.active_object
obj.name = 'BookWall'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.12, 2.5, 1.75)
if 'mat_BookDark' in dir():
    obj.data.materials.append(mat_BookDark)

# Object: BookShelf0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.7, -1.0, 0.4))
obj = bpy.context.active_object
obj.name = 'BookShelf0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 2.5, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BookShelf1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.7, -1.0, 0.95))
obj = bpy.context.active_object
obj.name = 'BookShelf1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 2.5, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BookShelf2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.7, -1.0, 1.5))
obj = bpy.context.active_object
obj.name = 'BookShelf2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 2.5, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BookShelf3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.7, -1.0, 2.05))
obj = bpy.context.active_object
obj.name = 'BookShelf3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 2.5, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BookShelf4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.7, -1.0, 2.6))
obj = bpy.context.active_object
obj.name = 'BookShelf4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 2.5, 0.02)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: Bench
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.2, -3.5, 0.35))
obj = bpy.context.active_object
obj.name = 'Bench'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.35, 0.04)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: BenchBack
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.45, -3.5, 0.75))
obj = bpy.context.active_object
obj.name = 'BenchBack'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.35, 0.4)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: KitchenCounter
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.5, 3.0, 0.45))
obj = bpy.context.active_object
obj.name = 'KitchenCounter'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.4, 0.4, 0.45)
if 'mat_StainlessSteel' in dir():
    obj.data.materials.append(mat_StainlessSteel)

# Object: Stove
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.2, 3.3, 0.9))
obj = bpy.context.active_object
obj.name = 'Stove'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.3, 0.04)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Fridge
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.8, 3.6, 1.0))
obj = bpy.context.active_object
obj.name = 'Fridge'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.35, 1.0)
if 'mat_StainlessSteel' in dir():
    obj.data.materials.append(mat_StainlessSteel)

# Object: Cord0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -2.5, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant0
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(-3.2, -2.5, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.15)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Cord1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -2.5, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant1
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(-1.5, -2.5, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.15)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Cord2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.2, -1.0, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant2
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(-3.2, -1.0, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.15)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Cord3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.5, -1.0, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant3
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(-1.5, -1.0, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.15)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Cord4
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.25, -1.5, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant4
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(1.25, -1.5, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.18)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Cord5
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.75, -1.5, 2.85))
obj = bpy.context.active_object
obj.name = 'Cord5'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.008, 0.008, 0.65)
if 'mat_Cord' in dir():
    obj.data.materials.append(mat_Cord)

# Object: Pendant5
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(2.75, -1.5, 2.1))
obj = bpy.context.active_object
obj.name = 'Pendant5'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.18)
if 'mat_Brass' in dir():
    obj.data.materials.append(mat_Brass)

# Object: Pot0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-4.0, -3.7, 0.2))
obj = bpy.context.active_object
obj.name = 'Pot0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.2)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: Plant0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-4.0, -3.7, 0.7))
obj = bpy.context.active_object
obj.name = 'Plant0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 0.35, 0.4)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: Pot1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.3, 0.0, 0.2))
obj = bpy.context.active_object
obj.name = 'Pot1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.16, 0.16, 0.2)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: Plant1
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(0.3, 0.0, 0.65))
obj = bpy.context.active_object
obj.name = 'Plant1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.3, 0.35)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)

# Object: Pot2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-4.2, 2.0, 0.2))
obj = bpy.context.active_object
obj.name = 'Pot2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.2, 0.2, 0.2)
if 'mat_Terracotta' in dir():
    obj.data.materials.append(mat_Terracotta)

# Object: Plant2
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-4.2, 2.0, 0.75))
obj = bpy.context.active_object
obj.name = 'Plant2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.45)
if 'mat_Foliage' in dir():
    obj.data.materials.append(mat_Foliage)



# ════════════════════════════════════════════════════════════════
# MULTI-ANGLE RENDER — parametric (room dims auto-fit cameras)
# ════════════════════════════════════════════════════════════════
import json
from pathlib import Path
import mathutils

ROOM_LEN = 10.0
ROOM_WID = 8.0
ROOM_HT  = 3.5

# Tone down world ambient
if world and world.node_tree:
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.45, 0.48, 0.52, 1.0)
        bg.inputs[1].default_value = 0.8

# ── Lighting ────────────────────────────────────────────────────
sun = bpy.data.lights.new(name='SunMain', type='SUN')
sun.energy = 4.0
sun.color = (1.0, 0.96, 0.9)
sun.angle = 0.05
sun_obj = bpy.data.objects.new('SunMain', sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.location = (ROOM_LEN * 0.4, -ROOM_WID * 0.5, ROOM_HT * 4)
sun_obj.rotation_euler = (math.radians(35.0), math.radians(15.0), math.radians(-30.0))

# Ceiling grid lights (3 × 2)
for fx in [-0.35, 0.0, 0.35]:
    for fy in [-0.3, 0.3]:
        al = bpy.data.lights.new(name=f'Ceil_{fx}_{fy}', type='AREA')
        al.energy = 150.0
        al.color = (1.0, 0.97, 0.93)
        al.size = 1.5
        al_obj = bpy.data.objects.new(f'Ceil_{fx}_{fy}', al)
        bpy.context.collection.objects.link(al_obj)
        al_obj.location = (ROOM_LEN * fx, ROOM_WID * fy, ROOM_HT - 0.15)

# Warm accent
warm = bpy.data.lights.new(name='WarmAccent', type='AREA')
warm.energy = 100.0
warm.color = (1.0, 0.82, 0.55)
warm.size = 1.0
warm_obj = bpy.data.objects.new('WarmAccent', warm)
bpy.context.collection.objects.link(warm_obj)
warm_obj.location = (ROOM_LEN * 0.3, ROOM_WID * 0.4, ROOM_HT - 0.4)

scene.eevee.taa_render_samples = 128
scene.eevee.use_bloom = True
scene.eevee.use_ssr = True
scene.eevee.use_gtao = True
scene.eevee.gtao_distance = 1.5
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium Contrast'
scene.view_settings.exposure = -0.5

# ── Cameras (auto-scaled to room) ───────────────────────────────
RENDER_DIR = Path(r'/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/03-coffee-shop/renders')
RENDER_DIR.mkdir(parents=True, exist_ok=True)

HX = ROOM_LEN / 2 - 0.6   # half-x margin
HY = ROOM_WID / 2 - 0.6   # half-y margin

# (name, location, target, lens, ortho?, hide_ceiling, hide_walls)
SHOTS = [
    ('01_hero_corner',   ( HX, -HY, 2.2),                     (-HX*0.5,  HY*0.4, 1.0), 22, False, False, []),
    ('02_reception',     (-HX,  HY*0.6, 1.7),                 (-HX*0.4,  HY*0.1, 1.2), 28, False, False, []),
    ('03_main_zone',     ( HX*0.7,  HY*0.7, 1.7),             (0.0, -HY*0.1, 1.0),     28, False, False, []),
    ('04_feature_zone',  ( HX*0.9, -HY*0.3, 1.7),             ( HX*0.5,  HY*0.3, 1.2), 24, False, False, []),
    ('05_lounge_zone',   (-HX*0.4,  HY, 1.7),                 ( HX*0.7, -HY*0.7, 1.0), 28, False, False, []),
    ('06_back_corner',   ( HX*0.2, -HY, 1.7),                 (-HX*0.5, -HY*0.7, 1.4), 35, False, False, []),
    ('07_top_ortho',     ( 0.0,  0.0, ROOM_HT * 4),           (0.0, 0.0, 0.0),         None, True, True, ['Wall_North','Wall_South','Wall_East','Wall_West']),
    ('08_birds_eye_3d',  (-ROOM_LEN, -ROOM_WID, ROOM_HT*3),   (0.0, 0.0, 0.5),         35, False, True, ['Wall_South','Wall_West']),
]

def look_at(cam_obj, target):
    direction = mathutils.Vector(target) - mathutils.Vector(cam_obj.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def hide(name, hidden=True):
    o = bpy.data.objects.get(name)
    if o:
        o.hide_render = hidden

scene.render.image_settings.file_format = 'PNG'

for name, loc, target, lens, is_ortho, hide_ceil, hide_walls in SHOTS:
    cam_data = bpy.data.cameras.new(name=f'Cam_{name}')
    if is_ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = max(ROOM_LEN, ROOM_WID) * 1.1
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = lens
        cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.05
    cam_data.clip_end = 200.0
    cam_obj = bpy.data.objects.new(f'Cam_{name}', cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = loc
    look_at(cam_obj, target)
    scene.camera = cam_obj
    if hide_ceil: hide('Ceiling', True)
    for w in hide_walls: hide(w, True)
    out = RENDER_DIR / f'{name}.png'
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(f'[OK] {out}')
    if hide_ceil: hide('Ceiling', False)
    for w in hide_walls: hide(w, False)

print('=== Multi-angle render complete ===')

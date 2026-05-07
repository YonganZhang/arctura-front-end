#!/usr/bin/env python3
"""Auto-generated Blender Python export script from blender-cli."""

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
mat_WallBlack = bpy.data.materials.new(name='WallBlack')
mat_WallBlack.use_nodes = True
bsdf_WallBlack = mat_WallBlack.node_tree.nodes.get('Principled BSDF')
if bsdf_WallBlack:
    bsdf_WallBlack.inputs['Base Color'].default_value = (0.102, 0.102, 0.11, 1.0)
    bsdf_WallBlack.inputs['Metallic'].default_value = 0.0
    bsdf_WallBlack.inputs['Roughness'].default_value = 0.85
    bsdf_WallBlack.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WallBlack.inputs['Alpha'].default_value = 1.0

mat_MirrorSilver = bpy.data.materials.new(name='MirrorSilver')
mat_MirrorSilver.use_nodes = True
bsdf_MirrorSilver = mat_MirrorSilver.node_tree.nodes.get('Principled BSDF')
if bsdf_MirrorSilver:
    bsdf_MirrorSilver.inputs['Base Color'].default_value = (0.784, 0.804, 0.823, 1.0)
    bsdf_MirrorSilver.inputs['Metallic'].default_value = 0.95
    bsdf_MirrorSilver.inputs['Roughness'].default_value = 0.05
    bsdf_MirrorSilver.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_MirrorSilver.inputs['Alpha'].default_value = 1.0

mat_PowerYellow = bpy.data.materials.new(name='PowerYellow')
mat_PowerYellow.use_nodes = True
bsdf_PowerYellow = mat_PowerYellow.node_tree.nodes.get('Principled BSDF')
if bsdf_PowerYellow:
    bsdf_PowerYellow.inputs['Base Color'].default_value = (0.898, 0.773, 0.278, 1.0)
    bsdf_PowerYellow.inputs['Metallic'].default_value = 0.0
    bsdf_PowerYellow.inputs['Roughness'].default_value = 0.6
    bsdf_PowerYellow.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_PowerYellow.inputs['Alpha'].default_value = 1.0

mat_WarmWood = bpy.data.materials.new(name='WarmWood')
mat_WarmWood.use_nodes = True
bsdf_WarmWood = mat_WarmWood.node_tree.nodes.get('Principled BSDF')
if bsdf_WarmWood:
    bsdf_WarmWood.inputs['Base Color'].default_value = (0.545, 0.435, 0.306, 1.0)
    bsdf_WarmWood.inputs['Metallic'].default_value = 0.0
    bsdf_WarmWood.inputs['Roughness'].default_value = 0.55
    bsdf_WarmWood.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WarmWood.inputs['Alpha'].default_value = 1.0

mat_Cream = bpy.data.materials.new(name='Cream')
mat_Cream.use_nodes = True
bsdf_Cream = mat_Cream.node_tree.nodes.get('Principled BSDF')
if bsdf_Cream:
    bsdf_Cream.inputs['Base Color'].default_value = (0.929, 0.91, 0.871, 1.0)
    bsdf_Cream.inputs['Metallic'].default_value = 0.0
    bsdf_Cream.inputs['Roughness'].default_value = 0.9
    bsdf_Cream.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Cream.inputs['Alpha'].default_value = 1.0

mat_DeepRed = bpy.data.materials.new(name='DeepRed')
mat_DeepRed.use_nodes = True
bsdf_DeepRed = mat_DeepRed.node_tree.nodes.get('Principled BSDF')
if bsdf_DeepRed:
    bsdf_DeepRed.inputs['Base Color'].default_value = (0.635, 0.231, 0.188, 1.0)
    bsdf_DeepRed.inputs['Metallic'].default_value = 0.0
    bsdf_DeepRed.inputs['Roughness'].default_value = 0.65
    bsdf_DeepRed.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_DeepRed.inputs['Alpha'].default_value = 1.0

mat_BlackMetal = bpy.data.materials.new(name='BlackMetal')
mat_BlackMetal.use_nodes = True
bsdf_BlackMetal = mat_BlackMetal.node_tree.nodes.get('Principled BSDF')
if bsdf_BlackMetal:
    bsdf_BlackMetal.inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1.0)
    bsdf_BlackMetal.inputs['Metallic'].default_value = 0.85
    bsdf_BlackMetal.inputs['Roughness'].default_value = 0.3
    bsdf_BlackMetal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_BlackMetal.inputs['Alpha'].default_value = 1.0

mat_RubberFloor = bpy.data.materials.new(name='RubberFloor')
mat_RubberFloor.use_nodes = True
bsdf_RubberFloor = mat_RubberFloor.node_tree.nodes.get('Principled BSDF')
if bsdf_RubberFloor:
    bsdf_RubberFloor.inputs['Base Color'].default_value = (0.15, 0.15, 0.17, 1.0)
    bsdf_RubberFloor.inputs['Metallic'].default_value = 0.0
    bsdf_RubberFloor.inputs['Roughness'].default_value = 0.95
    bsdf_RubberFloor.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_RubberFloor.inputs['Alpha'].default_value = 1.0

mat_LockerGrey = bpy.data.materials.new(name='LockerGrey')
mat_LockerGrey.use_nodes = True
bsdf_LockerGrey = mat_LockerGrey.node_tree.nodes.get('Principled BSDF')
if bsdf_LockerGrey:
    bsdf_LockerGrey.inputs['Base Color'].default_value = (0.35, 0.36, 0.38, 1.0)
    bsdf_LockerGrey.inputs['Metallic'].default_value = 0.2
    bsdf_LockerGrey.inputs['Roughness'].default_value = 0.5
    bsdf_LockerGrey.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_LockerGrey.inputs['Alpha'].default_value = 1.0

mat_YogaMat = bpy.data.materials.new(name='YogaMat')
mat_YogaMat.use_nodes = True
bsdf_YogaMat = mat_YogaMat.node_tree.nodes.get('Principled BSDF')
if bsdf_YogaMat:
    bsdf_YogaMat.inputs['Base Color'].default_value = (0.55, 0.3, 0.28, 1.0)
    bsdf_YogaMat.inputs['Metallic'].default_value = 0.0
    bsdf_YogaMat.inputs['Roughness'].default_value = 0.9
    bsdf_YogaMat.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_YogaMat.inputs['Alpha'].default_value = 1.0

mat_WoodFloor = bpy.data.materials.new(name='WoodFloor')
mat_WoodFloor.use_nodes = True
bsdf_WoodFloor = mat_WoodFloor.node_tree.nodes.get('Principled BSDF')
if bsdf_WoodFloor:
    bsdf_WoodFloor.inputs['Base Color'].default_value = (0.62, 0.5, 0.36, 1.0)
    bsdf_WoodFloor.inputs['Metallic'].default_value = 0.0
    bsdf_WoodFloor.inputs['Roughness'].default_value = 0.55
    bsdf_WoodFloor.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WoodFloor.inputs['Alpha'].default_value = 1.0

mat_Glass = bpy.data.materials.new(name='Glass')
mat_Glass.use_nodes = True
bsdf_Glass = mat_Glass.node_tree.nodes.get('Principled BSDF')
if bsdf_Glass:
    bsdf_Glass.inputs['Base Color'].default_value = (0.85, 0.9, 0.92, 1.0)
    bsdf_Glass.inputs['Metallic'].default_value = 0.0
    bsdf_Glass.inputs['Roughness'].default_value = 0.1
    bsdf_Glass.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Glass.inputs['Alpha'].default_value = 1.0

mat_BrassAccent = bpy.data.materials.new(name='BrassAccent')
mat_BrassAccent.use_nodes = True
bsdf_BrassAccent = mat_BrassAccent.node_tree.nodes.get('Principled BSDF')
if bsdf_BrassAccent:
    bsdf_BrassAccent.inputs['Base Color'].default_value = (0.72, 0.6, 0.35, 1.0)
    bsdf_BrassAccent.inputs['Metallic'].default_value = 0.9
    bsdf_BrassAccent.inputs['Roughness'].default_value = 0.25
    bsdf_BrassAccent.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_BrassAccent.inputs['Alpha'].default_value = 1.0


# ── Objects ─────────────────────────────────────────────────
# Object: FloorMain
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
obj = bpy.context.active_object
obj.name = 'FloorMain'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (10.0, 10.0, 0.1)
if 'mat_RubberFloor' in dir():
    obj.data.materials.append(mat_RubberFloor)

# Object: FloorYoga
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.5, -2.5, 0.05))
obj = bpy.context.active_object
obj.name = 'FloorYoga'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (5.0, 5.0, 0.05)
if 'mat_WoodFloor' in dir():
    obj.data.materials.append(mat_WoodFloor)

# Object: Ceiling
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 3.5))
obj = bpy.context.active_object
obj.name = 'Ceiling'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (10.0, 10.0, 0.1)
if 'mat_WallBlack' in dir():
    obj.data.materials.append(mat_WallBlack)

# Object: WallNorth
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 5.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallNorth'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (10.0, 0.15, 3.5)
if 'mat_WallBlack' in dir():
    obj.data.materials.append(mat_WallBlack)

# Object: WallSouth
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, -5.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallSouth'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (10.0, 0.15, 3.5)
if 'mat_WallBlack' in dir():
    obj.data.materials.append(mat_WallBlack)

# Object: WallEastMirror
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(5.0, 0.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallEastMirror'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 10.0, 3.5)
if 'mat_MirrorSilver' in dir():
    obj.data.materials.append(mat_MirrorSilver)

# Object: WallWest
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-5.0, 0.0, 1.75))
obj = bpy.context.active_object
obj.name = 'WallWest'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 10.0, 3.5)
if 'mat_WallBlack' in dir():
    obj.data.materials.append(mat_WallBlack)

# Object: MirrorPanel
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.92, 0.0, 1.75))
obj = bpy.context.active_object
obj.name = 'MirrorPanel'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.04, 9.6, 3.2)
if 'mat_MirrorSilver' in dir():
    obj.data.materials.append(mat_MirrorSilver)

# Object: ReceptionDesk
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.5, -4.2, 0.55))
obj = bpy.context.active_object
obj.name = 'ReceptionDesk'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.8, 0.7, 1.1)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ReceptionStool
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.5, -3.7, 0.45))
obj = bpy.context.active_object
obj.name = 'ReceptionStool'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.3, 0.3, 0.9)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: WaitChair1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0, -4.5, 0.45))
obj = bpy.context.active_object
obj.name = 'WaitChair1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.55, 0.55, 0.9)
if 'mat_DeepRed' in dir():
    obj.data.materials.append(mat_DeepRed)

# Object: WaitChair2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.2, -4.5, 0.45))
obj = bpy.context.active_object
obj.name = 'WaitChair2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.55, 0.55, 0.9)
if 'mat_DeepRed' in dir():
    obj.data.materials.append(mat_DeepRed)

# Object: LogoPanel
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.5, -4.92, 2.0))
obj = bpy.context.active_object
obj.name = 'LogoPanel'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.2, 0.05, 1.2)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: Locker0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, -2.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, -1.75, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, -1.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, -0.75, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, -0.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker5
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, 0.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker5'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker6
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, 0.75, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker6'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker7
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, 1.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker7'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker8
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, 1.75, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker8'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: Locker9
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.6, 2.25, 1.0))
obj = bpy.context.active_object
obj.name = 'Locker9'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 2.0)
if 'mat_LockerGrey' in dir():
    obj.data.materials.append(mat_LockerGrey)

# Object: LockerBench
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.8, 0.0, 0.22))
obj = bpy.context.active_object
obj.name = 'LockerBench'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 2.4, 0.45)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: LiftPlatform1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.5, -3.0, 0.12))
obj = bpy.context.active_object
obj.name = 'LiftPlatform1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 1.5, 0.05)
if 'mat_RubberFloor' in dir():
    obj.data.materials.append(mat_RubberFloor)

# Object: LiftPlatform2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.5, -1.0, 0.12))
obj = bpy.context.active_object
obj.name = 'LiftPlatform2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 1.5, 0.05)
if 'mat_RubberFloor' in dir():
    obj.data.materials.append(mat_RubberFloor)

# Object: DumbbellRack
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.3, 0.5, 0.9))
obj = bpy.context.active_object
obj.name = 'DumbbellRack'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 3.0, 1.5)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: DmbShelf1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.3, 0.5, 0.5))
obj = bpy.context.active_object
obj.name = 'DmbShelf1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 2.9, 0.04)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: DmbShelf2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.3, 0.5, 0.95))
obj = bpy.context.active_object
obj.name = 'DmbShelf2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 2.9, 0.04)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: DmbShelf3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.3, 0.5, 1.4))
obj = bpy.context.active_object
obj.name = 'DmbShelf3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 2.9, 0.04)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s1_k0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.7, 0.58))
obj = bpy.context.active_object
obj.name = 'Dmb_s1_k0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s1_k1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.09999999999999998, 0.58))
obj = bpy.context.active_object
obj.name = 'Dmb_s1_k1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s1_k2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 0.5, 0.58))
obj = bpy.context.active_object
obj.name = 'Dmb_s1_k2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s1_k3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 1.0999999999999999, 0.58))
obj = bpy.context.active_object
obj.name = 'Dmb_s1_k3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s2_k0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.7, 1.03))
obj = bpy.context.active_object
obj.name = 'Dmb_s2_k0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s2_k1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.09999999999999998, 1.03))
obj = bpy.context.active_object
obj.name = 'Dmb_s2_k1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s2_k2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 0.5, 1.03))
obj = bpy.context.active_object
obj.name = 'Dmb_s2_k2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s2_k3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 1.0999999999999999, 1.03))
obj = bpy.context.active_object
obj.name = 'Dmb_s2_k3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s3_k0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.7, 1.48))
obj = bpy.context.active_object
obj.name = 'Dmb_s3_k0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s3_k1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, -0.09999999999999998, 1.48))
obj = bpy.context.active_object
obj.name = 'Dmb_s3_k1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s3_k2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 0.5, 1.48))
obj = bpy.context.active_object
obj.name = 'Dmb_s3_k2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Dmb_s3_k3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.3, 1.0999999999999999, 1.48))
obj = bpy.context.active_object
obj.name = 'Dmb_s3_k3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.11, 0.11, 0.35)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -4.0, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -3.65, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -3.3, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -2.95, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -2.6, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: Barbell5
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.3, -2.25, 0.22))
obj = bpy.context.active_object
obj.name = 'Barbell5'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.0, 0.03, 0.03)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: WeightStack1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.8, -3.0, 0.3))
obj = bpy.context.active_object
obj.name = 'WeightStack1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: WeightStack2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(3.2, -3.0, 0.3))
obj = bpy.context.active_object
obj.name = 'WeightStack2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: WeightStack3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.8, -1.0, 0.3))
obj = bpy.context.active_object
obj.name = 'WeightStack3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: WeightStack4
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(3.2, -1.0, 0.3))
obj = bpy.context.active_object
obj.name = 'WeightStack4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.3)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: YogaMat_c0_r0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.3, -4.3, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c0_r0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: YogaMat_c0_r1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.3, -3.1999999999999997, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c0_r1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: YogaMat_c0_r2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.3, -2.0999999999999996, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c0_r2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: YogaMat_c1_r0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0999999999999996, -4.3, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c1_r0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: YogaMat_c1_r1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0999999999999996, -3.1999999999999997, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c1_r1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: YogaMat_c1_r2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.0999999999999996, -2.0999999999999996, 0.06))
obj = bpy.context.active_object
obj.name = 'YogaMat_c1_r2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.8, 0.5, 0.02)
if 'mat_YogaMat' in dir():
    obj.data.materials.append(mat_YogaMat)

# Object: PilatesReformer
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.0, -4.0, 0.25))
obj = bpy.context.active_object
obj.name = 'PilatesReformer'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.8, 0.4, 0.3)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: YogaBlocks
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.8, -2.8, 0.15))
obj = bpy.context.active_object
obj.name = 'YogaBlocks'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.15, 0.15)
if 'mat_PowerYellow' in dir():
    obj.data.materials.append(mat_PowerYellow)

# Object: ConsultTable
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.0, 3.5, 0.38))
obj = bpy.context.active_object
obj.name = 'ConsultTable'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.2, 0.8, 0.04)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: ConsultLeg1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.5, 3.1, 0.2))
obj = bpy.context.active_object
obj.name = 'ConsultLeg1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.05, 0.4)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ConsultLeg2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.5, 3.1, 0.2))
obj = bpy.context.active_object
obj.name = 'ConsultLeg2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.05, 0.4)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ConsultLeg3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.5, 3.9, 0.2))
obj = bpy.context.active_object
obj.name = 'ConsultLeg3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.05, 0.4)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ConsultLeg4
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.5, 3.9, 0.2))
obj = bpy.context.active_object
obj.name = 'ConsultLeg4'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.05, 0.4)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: ConsultChair1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.7, 4.3, 0.45))
obj = bpy.context.active_object
obj.name = 'ConsultChair1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.9)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: ConsultChair2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.3, 4.3, 0.45))
obj = bpy.context.active_object
obj.name = 'ConsultChair2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.5, 0.9)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: ShowerWall1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.0, 4.0, 1.25))
obj = bpy.context.active_object
obj.name = 'ShowerWall1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 2.0, 2.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: ShowerWall2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.5, 3.0, 1.25))
obj = bpy.context.active_object
obj.name = 'ShowerWall2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.5, 0.05, 2.5)
if 'mat_Glass' in dir():
    obj.data.materials.append(mat_Glass)

# Object: ShowerFloor1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.8, 4.2, 0.04))
obj = bpy.context.active_object
obj.name = 'ShowerFloor1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.7, 0.7, 0.05)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: ShowerFloor2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.8, 4.2, 0.04))
obj = bpy.context.active_object
obj.name = 'ShowerFloor2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.7, 0.7, 0.05)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: ShowerHead1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.8, 4.5, 2.2))
obj = bpy.context.active_object
obj.name = 'ShowerHead1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.08, 0.08, 0.1)
if 'mat_BrassAccent' in dir():
    obj.data.materials.append(mat_BrassAccent)

# Object: ShowerHead2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(3.8, 4.5, 2.2))
obj = bpy.context.active_object
obj.name = 'ShowerHead2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.08, 0.08, 0.1)
if 'mat_BrassAccent' in dir():
    obj.data.materials.append(mat_BrassAccent)

# Object: Sink
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.3, 3.5, 0.8))
obj = bpy.context.active_object
obj.name = 'Sink'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.5, 0.4, 0.1)
if 'mat_Cream' in dir():
    obj.data.materials.append(mat_Cream)

# Object: SinkMirror
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.6, 3.5, 1.5))
obj = bpy.context.active_object
obj.name = 'SinkMirror'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 0.4, 0.6)
if 'mat_MirrorSilver' in dir():
    obj.data.materials.append(mat_MirrorSilver)

# Object: StorageCabinet
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-4.2, 4.5, 1.0))
obj = bpy.context.active_object
obj.name = 'StorageCabinet'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.6, 0.8, 2.0)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: YogaBall1
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(-0.5, 3.8, 0.4))
obj = bpy.context.active_object
obj.name = 'YogaBall1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.4)
if 'mat_DeepRed' in dir():
    obj.data.materials.append(mat_DeepRed)

# Object: YogaBall2
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(0.0, 3.8, 0.4))
obj = bpy.context.active_object
obj.name = 'YogaBall2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.4, 0.4, 0.4)
if 'mat_DeepRed' in dir():
    obj.data.materials.append(mat_DeepRed)

# Object: FoamRoller1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(0.5, 3.8, 0.15))
obj = bpy.context.active_object
obj.name = 'FoamRoller1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.45)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: FoamRoller2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.0, 3.8, 0.15))
obj = bpy.context.active_object
obj.name = 'FoamRoller2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.15, 0.45)
if 'mat_WarmWood' in dir():
    obj.data.materials.append(mat_WarmWood)

# Object: TrackLight_A0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.5, -1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_A0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_B0
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-3.5, 1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_B0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_A1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.0, -1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_A1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_B1
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(-1.0, 1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_B1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_A2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.5, -1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_A2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_B2
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(1.5, 1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_B2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_A3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.0, -1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_A3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: TrackLight_B3
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(4.0, 1.5, 3.4))
obj = bpy.context.active_object
obj.name = 'TrackLight_B3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.1, 0.1, 0.1)
if 'mat_BlackMetal' in dir():
    obj.data.materials.append(mat_BlackMetal)

# Object: AccentStripe
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 4.92, 2.8))
obj = bpy.context.active_object
obj.name = 'AccentStripe'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (3.0, 0.05, 0.15)
if 'mat_PowerYellow' in dir():
    obj.data.materials.append(mat_PowerYellow)

# Object: RedAccent
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(4.88, -4.0, 2.5))
obj = bpy.context.active_object
obj.name = 'RedAccent'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 1.2, 0.25)
if 'mat_DeepRed' in dir():
    obj.data.materials.append(mat_DeepRed)


# ── Cameras ─────────────────────────────────────────────────
cam_data = bpy.data.cameras.new(name='Camera')
cam_data.type = 'PERSP'
cam_data.lens = 18.0
cam_data.sensor_width = 36.0
cam_data.clip_start = 0.1
cam_data.clip_end = 1000.0
cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (4.2, -4.0, 2.0)
cam_obj.rotation_euler = (math.radians(78.0), math.radians(0.0), math.radians(45.0))
scene.camera = cam_obj


# ── Lights ──────────────────────────────────────────────────
light_data = bpy.data.lights.new(name='Area', type='AREA')
light_data.energy = 200.0
light_data.color = (1.0, 0.95, 0.85)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0.0, 0.0, 3.3)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Sun', type='SUN')
light_data.energy = 3.0
light_data.color = (1.0, 1.0, 0.98)
light_data.angle = 0.00918
light_obj = bpy.data.objects.new('Sun', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0.0, 0.0, 5.0)
light_obj.rotation_euler = (math.radians(30.0), math.radians(0.0), math.radians(20.0))

light_data = bpy.data.lights.new(name='Area.001', type='AREA')
light_data.energy = 120.0
light_data.color = (1.0, 0.98, 0.9)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area.001', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (3.0, 0.0, 3.2)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Area.002', type='AREA')
light_data.energy = 100.0
light_data.color = (1.0, 0.96, 0.88)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area.002', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (-3.0, -3.0, 3.2)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))


# ── Keyframes ───────────────────────────────────────────────
# (none)

# ── Export Output ───────────────────────────────────────────
out_path = r'/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/05-fitness-studio/exports/05-fitness-studio.glb'
os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')

print('Export complete: /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/05-fitness-studio/exports/05-fitness-studio.glb')
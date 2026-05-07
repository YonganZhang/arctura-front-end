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
scene.eevee.taa_render_samples = 128

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
mat_WoodFloor = bpy.data.materials.new(name='WoodFloor')
mat_WoodFloor.use_nodes = True
bsdf_WoodFloor = mat_WoodFloor.node_tree.nodes.get('Principled BSDF')
if bsdf_WoodFloor:
    bsdf_WoodFloor.inputs['Base Color'].default_value = (0.55, 0.42, 0.28, 1.0)
    bsdf_WoodFloor.inputs['Metallic'].default_value = 0.0
    bsdf_WoodFloor.inputs['Roughness'].default_value = 0.55
    bsdf_WoodFloor.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_WoodFloor.inputs['Alpha'].default_value = 1.0

mat_Wall = bpy.data.materials.new(name='Wall')
mat_Wall.use_nodes = True
bsdf_Wall = mat_Wall.node_tree.nodes.get('Principled BSDF')
if bsdf_Wall:
    bsdf_Wall.inputs['Base Color'].default_value = (0.92, 0.88, 0.82, 1.0)
    bsdf_Wall.inputs['Metallic'].default_value = 0.0
    bsdf_Wall.inputs['Roughness'].default_value = 0.9
    bsdf_Wall.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Wall.inputs['Alpha'].default_value = 1.0

mat_LightWood = bpy.data.materials.new(name='LightWood')
mat_LightWood.use_nodes = True
bsdf_LightWood = mat_LightWood.node_tree.nodes.get('Principled BSDF')
if bsdf_LightWood:
    bsdf_LightWood.inputs['Base Color'].default_value = (0.75, 0.62, 0.45, 1.0)
    bsdf_LightWood.inputs['Metallic'].default_value = 0.0
    bsdf_LightWood.inputs['Roughness'].default_value = 0.6
    bsdf_LightWood.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_LightWood.inputs['Alpha'].default_value = 1.0

mat_Charcoal = bpy.data.materials.new(name='Charcoal')
mat_Charcoal.use_nodes = True
bsdf_Charcoal = mat_Charcoal.node_tree.nodes.get('Principled BSDF')
if bsdf_Charcoal:
    bsdf_Charcoal.inputs['Base Color'].default_value = (0.18, 0.2, 0.22, 1.0)
    bsdf_Charcoal.inputs['Metallic'].default_value = 0.05
    bsdf_Charcoal.inputs['Roughness'].default_value = 0.6
    bsdf_Charcoal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Charcoal.inputs['Alpha'].default_value = 1.0

mat_Rug = bpy.data.materials.new(name='Rug')
mat_Rug.use_nodes = True
bsdf_Rug = mat_Rug.node_tree.nodes.get('Principled BSDF')
if bsdf_Rug:
    bsdf_Rug.inputs['Base Color'].default_value = (0.82, 0.75, 0.65, 1.0)
    bsdf_Rug.inputs['Metallic'].default_value = 0.0
    bsdf_Rug.inputs['Roughness'].default_value = 0.95
    bsdf_Rug.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Rug.inputs['Alpha'].default_value = 1.0

mat_Fabric = bpy.data.materials.new(name='Fabric')
mat_Fabric.use_nodes = True
bsdf_Fabric = mat_Fabric.node_tree.nodes.get('Principled BSDF')
if bsdf_Fabric:
    bsdf_Fabric.inputs['Base Color'].default_value = (0.78, 0.7, 0.58, 1.0)
    bsdf_Fabric.inputs['Metallic'].default_value = 0.0
    bsdf_Fabric.inputs['Roughness'].default_value = 0.98
    bsdf_Fabric.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Fabric.inputs['Alpha'].default_value = 1.0

mat_Metal = bpy.data.materials.new(name='Metal')
mat_Metal.use_nodes = True
bsdf_Metal = mat_Metal.node_tree.nodes.get('Principled BSDF')
if bsdf_Metal:
    bsdf_Metal.inputs['Base Color'].default_value = (0.35, 0.35, 0.38, 1.0)
    bsdf_Metal.inputs['Metallic'].default_value = 0.95
    bsdf_Metal.inputs['Roughness'].default_value = 0.3
    bsdf_Metal.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Metal.inputs['Alpha'].default_value = 1.0

mat_Shade = bpy.data.materials.new(name='Shade')
mat_Shade.use_nodes = True
bsdf_Shade = mat_Shade.node_tree.nodes.get('Principled BSDF')
if bsdf_Shade:
    bsdf_Shade.inputs['Base Color'].default_value = (0.95, 0.85, 0.65, 1.0)
    bsdf_Shade.inputs['Metallic'].default_value = 0.0
    bsdf_Shade.inputs['Roughness'].default_value = 0.7
    bsdf_Shade.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Shade.inputs['Alpha'].default_value = 1.0

mat_Screen = bpy.data.materials.new(name='Screen')
mat_Screen.use_nodes = True
bsdf_Screen = mat_Screen.node_tree.nodes.get('Principled BSDF')
if bsdf_Screen:
    bsdf_Screen.inputs['Base Color'].default_value = (0.05, 0.1, 0.15, 1.0)
    bsdf_Screen.inputs['Metallic'].default_value = 0.2
    bsdf_Screen.inputs['Roughness'].default_value = 0.3
    bsdf_Screen.inputs['Specular IOR Level'].default_value = 0.5
    bsdf_Screen.inputs['Alpha'].default_value = 1.0


# ── Objects ─────────────────────────────────────────────────
# Object: Floor
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, 0.0, 0.0))
obj = bpy.context.active_object
obj.name = 'Floor'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.5, 2.0, 1.0)
if 'mat_WoodFloor' in dir():
    obj.data.materials.append(mat_WoodFloor)

# Object: BackWall
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 2.0, 1.4))
obj = bpy.context.active_object
obj.name = 'BackWall'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.5, 0.05, 1.4)
if 'mat_Wall' in dir():
    obj.data.materials.append(mat_Wall)

# Object: LeftWall
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.5, 0.0, 1.4))
obj = bpy.context.active_object
obj.name = 'LeftWall'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.05, 2.0, 1.4)
if 'mat_Wall' in dir():
    obj.data.materials.append(mat_Wall)

# Object: Bookshelf
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 1.65, 1.2))
obj = bpy.context.active_object
obj.name = 'Bookshelf'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.2, 0.175, 1.2)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: Shelf0
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 1.55, 0.5))
obj = bpy.context.active_object
obj.name = 'Shelf0'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.25, 0.02)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: Shelf1
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 1.55, 1.05))
obj = bpy.context.active_object
obj.name = 'Shelf1'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.25, 0.02)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: Shelf2
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 1.55, 1.6))
obj = bpy.context.active_object
obj.name = 'Shelf2'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.25, 0.02)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: Shelf3
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 1.55, 2.15))
obj = bpy.context.active_object
obj.name = 'Shelf3'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (2.15, 0.25, 0.02)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: Desk
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.4, -0.5, 0.75))
obj = bpy.context.active_object
obj.name = 'Desk'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (1.0, 0.35, 0.02)
if 'mat_LightWood' in dir():
    obj.data.materials.append(mat_LightWood)

# Object: DeskLegL
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-2.35, -0.5, 0.375))
obj = bpy.context.active_object
obj.name = 'DeskLegL'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.025, 0.35, 0.375)
if 'mat_Metal' in dir():
    obj.data.materials.append(mat_Metal)

# Object: DeskLegR
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-0.45, -0.5, 0.375))
obj = bpy.context.active_object
obj.name = 'DeskLegR'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.025, 0.35, 0.375)
if 'mat_Metal' in dir():
    obj.data.materials.append(mat_Metal)

# Object: Chair
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.4, -1.0, 0.45))
obj = bpy.context.active_object
obj.name = 'Chair'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.25, 0.025)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ChairBack
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.4, -1.25, 0.75))
obj = bpy.context.active_object
obj.name = 'ChairBack'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.03, 0.3)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: ArmChair
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.5, -1.2, 0.35))
obj = bpy.context.active_object
obj.name = 'ArmChair'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.4, 0.35)
if 'mat_Fabric' in dir():
    obj.data.materials.append(mat_Fabric)

# Object: ArmBack
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1.5, -1.55, 0.8))
obj = bpy.context.active_object
obj.name = 'ArmBack'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.45, 0.05, 0.45)
if 'mat_Fabric' in dir():
    obj.data.materials.append(mat_Fabric)

# Object: LampPole
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, vertices=32, location=(2.3, -1.5, 0.85))
obj = bpy.context.active_object
obj.name = 'LampPole'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.02, 0.02, 0.85)
if 'mat_Metal' in dir():
    obj.data.materials.append(mat_Metal)

# Object: LampShade
bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.0, depth=2.0, vertices=32, location=(2.3, -1.5, 1.75))
obj = bpy.context.active_object
obj.name = 'LampShade'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.18, 0.18, 0.15)
if 'mat_Shade' in dir():
    obj.data.materials.append(mat_Shade)

# Object: Rug
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(1.3, -1.0, 0.005))
obj = bpy.context.active_object
obj.name = 'Rug'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.9, 0.8, 1.0)
if 'mat_Rug' in dir():
    obj.data.materials.append(mat_Rug)

# Object: Cabinet
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.0, 1.55, 0.5))
obj = bpy.context.active_object
obj.name = 'Cabinet'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.35, 0.2, 0.5)
if 'mat_Charcoal' in dir():
    obj.data.materials.append(mat_Charcoal)

# Object: Laptop
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.4, -0.5, 0.78))
obj = bpy.context.active_object
obj.name = 'Laptop'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.15, 0.1, 0.01)
if 'mat_Screen' in dir():
    obj.data.materials.append(mat_Screen)

# Object: Monitor
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-1.0, -0.3, 1.05))
obj = bpy.context.active_object
obj.name = 'Monitor'
obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))
obj.scale = (0.25, 0.02, 0.15)
if 'mat_Screen' in dir():
    obj.data.materials.append(mat_Screen)


# ── Cameras ─────────────────────────────────────────────────
cam_data = bpy.data.cameras.new(name='Camera')
cam_data.type = 'PERSP'
cam_data.lens = 24.0
cam_data.sensor_width = 36.0
cam_data.clip_start = 0.1
cam_data.clip_end = 1000.0
cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (3.8, -3.2, 1.7)
cam_obj.rotation_euler = (math.radians(78.0), math.radians(0.0), math.radians(55.0))
scene.camera = cam_obj


# ── Lights ──────────────────────────────────────────────────
light_data = bpy.data.lights.new(name='Sun', type='SUN')
light_data.energy = 3.0
light_data.color = (1.0, 0.95, 0.85)
light_data.angle = 0.00918
light_obj = bpy.data.objects.new('Sun', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0.0, 0.0, 3.0)
light_obj.rotation_euler = (math.radians(-40.0), math.radians(15.0), math.radians(-30.0))

light_data = bpy.data.lights.new(name='Area', type='AREA')
light_data.energy = 100.0
light_data.color = (1.0, 0.95, 0.85)
light_data.size = 1.0
light_data.size_y = 1.0
light_data.shape = 'RECTANGLE'
light_obj = bpy.data.objects.new('Area', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0.0, -1.5, 2.6)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))

light_data = bpy.data.lights.new(name='Point', type='POINT')
light_data.energy = 60.0
light_data.color = (1.0, 0.8, 0.5)
light_data.shadow_soft_size = 0.25
light_obj = bpy.data.objects.new('Point', light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (2.3, -1.5, 1.7)
light_obj.rotation_euler = (math.radians(0.0), math.radians(0.0), math.radians(0.0))


# ── Keyframes ───────────────────────────────────────────────
# (none)

# ── Render Output ───────────────────────────────────────────
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = r'/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/render.png'
scene.frame_set(1)

# Render single frame
bpy.ops.render.render(write_still=True)

print('Render complete: /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/render.png')
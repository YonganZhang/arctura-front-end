
# ════════════════════════════════════════════════════════════════
# MULTI-ANGLE RENDER — parametric (room dims auto-fit cameras)
# ════════════════════════════════════════════════════════════════
import json
from pathlib import Path
import mathutils

ROOM_LEN = __ROOM_LEN__
ROOM_WID = __ROOM_WID__
ROOM_HT  = __ROOM_HT__

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
RENDER_DIR = Path(r'__RENDER_DIR__')
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

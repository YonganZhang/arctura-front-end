#!/usr/bin/env bash
# Build MVP 13 Stack Lab Blender scene.
# Room: 13m x 10m x 3m, center at origin.
# Layout (top-down, x=east, y=north):
#   - Entry + LOGO wall: SW corner (x=-5..-3, y=-5..-3)
#   - Reception: SE entry area (x=-3..0, y=-5..-3)
#   - Open desks 10 stations: central-west (x=-5..0, y=-2..3), 2 rows × 5
#   - GPU server room: NE corner glass (x=3..6.5, y=2..5)
#   - Glass meeting room: SE (x=2..6.5, y=-5..-1)
#   - 2 phone booths: E wall middle (x=5..6, y=0..1.2)
#   - Kitchenette: NW corner (x=-6.5..-4, y=3..5)
#   - Lounge + foosball: center-south (x=0..3, y=-2..2)
#   - Bathroom: far NW (x=-6.5..-5, y=-2..0)
#   - Plants: scattered

set -e
cd /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office

B() { cli-anything-blender --project room.json "$@"; }

# 1. Scene (first call has no --project, creates room.json)
cli-anything-blender scene new --name "StackLab" -o room.json

# 2. Materials (14 materials)
B material create --name Concrete      --color 0.71,0.69,0.66,1 --metallic 0.05 --roughness 0.7
B material create --name WarmWood      --color 0.55,0.42,0.30,1 --metallic 0.0  --roughness 0.5
B material create --name DeepTeal      --color 0.18,0.33,0.33,1 --metallic 0.2  --roughness 0.5
B material create --name SoftWhite     --color 0.94,0.93,0.89,1 --metallic 0.0  --roughness 0.85
B material create --name LimeGreen     --color 0.66,0.79,0.28,1 --metallic 0.1  --roughness 0.6
B material create --name Charcoal      --color 0.16,0.16,0.17,1 --metallic 0.3  --roughness 0.45
B material create --name Glass         --color 0.82,0.90,0.95,1 --metallic 0.2  --roughness 0.05
B material create --name ScreenDark    --color 0.05,0.06,0.10,1 --metallic 0.1  --roughness 0.2
B material create --name LED_Blue      --color 0.15,0.55,0.95,1 --metallic 0.7  --roughness 0.15
B material create --name Foliage       --color 0.22,0.50,0.26,1 --metallic 0.0  --roughness 0.85
B material create --name Terracotta    --color 0.60,0.35,0.25,1 --metallic 0.0  --roughness 0.7
B material create --name Steel         --color 0.70,0.72,0.75,1 --metallic 0.92 --roughness 0.3
B material create --name LogoAccent    --color 0.66,0.79,0.28,1 --metallic 0.4  --roughness 0.3
B material create --name Whiteboard    --color 0.97,0.97,0.95,1 --metallic 0.05 --roughness 0.2

# Material indices
M_CONCRETE=0; M_WOOD=1; M_TEAL=2; M_WHITE=3; M_LIME=4; M_CHAR=5
M_GLASS=6; M_SCREEN=7; M_LED=8; M_FOLIAGE=9; M_POT=10; M_STEEL=11; M_LOGO=12; M_WB=13

# 3. Shell (6 objects)
# Floor 13x10, walls around perimeter. Room center origin. Height 3m.
B object add plane  --name Floor      -l 0,0,0      -s 6.5,5.0,1
B object add cube   --name WallN      -l 0,5,1.5    -s 6.5,0.05,1.5
B object add cube   --name WallS      -l 0,-5,1.5   -s 6.5,0.05,1.5
B object add cube   --name WallW      -l -6.5,0,1.5 -s 0.05,5.0,1.5
B object add cube   --name WallE      -l 6.5,0,1.5  -s 0.05,5.0,1.5
B object add plane  --name Ceiling    -l 0,0,3      -s 6.5,5.0,1

B material assign $M_CONCRETE 0   # Floor
B material assign $M_WHITE 1       # WallN
B material assign $M_WHITE 2       # WallS
B material assign $M_WHITE 3       # WallW
B material assign $M_WHITE 4       # WallE
B material assign $M_WHITE 5       # Ceiling

# 4. Entry + LOGO wall (5 objects): positions 6..10
# LOGO backing panel on south wall
B object add cube --name LogoPanel      -l -4.5,-4.9,1.8  -s 1.5,0.05,0.8
B object add cube --name LogoAccentBar  -l -4.5,-4.85,1.8 -s 1.3,0.04,0.08
B object add cube --name ReceptionDesk  -l -2.0,-3.7,0.55 -s 1.0,0.5,0.55
B object add cube --name WaitBench      -l -5.5,-3.5,0.25 -s 0.8,0.3,0.25
B object add cube --name EntryMat       -l -4.5,-4.3,0.01 -s 0.7,0.4,0.01
B material assign $M_CHAR 6
B material assign $M_LIME 7
B material assign $M_WOOD 8
B material assign $M_WOOD 9
B material assign $M_TEAL 10

# 5. Open desks: 10 stations, 2 rows of 5
# Row 1 (y=-1): desks at x = -5, -3.5, -2, -0.5, 1.0 (spaced 1.5m)
# Row 2 (y=1.5): same x
# Each station: desk, chair, 2 screens = 4 objects × 10 = 40
# That alone blows past 60. Good.
# Index starts at 11.
IDX=11
for row in "-1.5" "1.8"; do
  for i in 0 1 2 3 4; do
    x=$(python3 -c "print(-5 + $i * 1.4)")
    # Desk (top)
    B object add cube --name "Desk_r${row}_${i}"     -l ${x},${row},0.75 -s 0.6,0.35,0.02
    B material assign $M_WOOD $IDX; IDX=$((IDX+1))
    # Chair
    B object add cube --name "Chair_r${row}_${i}"    -l ${x},$(python3 -c "print($row - 0.6 if $row < 0 else $row + 0.6)"),0.45 -s 0.25,0.25,0.03
    B material assign $M_CHAR $IDX; IDX=$((IDX+1))
    # Screen L
    B object add cube --name "ScrL_r${row}_${i}"     -l $(python3 -c "print($x - 0.2)"),${row},1.15 -s 0.22,0.02,0.16
    B material assign $M_SCREEN $IDX; IDX=$((IDX+1))
    # Screen R
    B object add cube --name "ScrR_r${row}_${i}"     -l $(python3 -c "print($x + 0.2)"),${row},1.15 -s 0.22,0.02,0.16
    B material assign $M_SCREEN $IDX; IDX=$((IDX+1))
  done
done

# Divider strip between the 2 rows of desks (visual separation)
B object add cube --name DeskDivider -l -2.0,0.15,1.1 -s 4.3,0.02,0.35
B material assign $M_TEAL $IDX; IDX=$((IDX+1))

# 6. GPU server room (NE corner, glass-walled): 3 racks + glass
# Glass partition: 2 walls (N side open since uses room wallN)
B object add cube --name GPU_GlassW  -l 3.0,3.5,1.5   -s 0.03,1.5,1.5
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
B object add cube --name GPU_GlassS  -l 4.75,2.0,1.5  -s 1.75,0.03,1.5
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
B object add cube --name GPU_Door    -l 3.03,2.0,1.05 -s 0.02,0.35,1.05
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
# 3 server racks (cubes, each 0.6 × 1.0 × 2.0)
B object add cube --name Rack1       -l 3.8,3.8,1.0   -s 0.3,0.5,1.0
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cube --name Rack2       -l 4.8,3.8,1.0   -s 0.3,0.5,1.0
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cube --name Rack3       -l 5.8,3.8,1.0   -s 0.3,0.5,1.0
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
# Blue LED accent strips on top of each rack
B object add cube --name LED1        -l 3.8,3.8,2.02  -s 0.28,0.48,0.02
B material assign $M_LED $IDX; IDX=$((IDX+1))
B object add cube --name LED2        -l 4.8,3.8,2.02  -s 0.28,0.48,0.02
B material assign $M_LED $IDX; IDX=$((IDX+1))
B object add cube --name LED3        -l 5.8,3.8,2.02  -s 0.28,0.48,0.02
B material assign $M_LED $IDX; IDX=$((IDX+1))
# LED status strip side light (vertical accent)
B object add cube --name LEDstrip    -l 3.05,2.5,1.5  -s 0.02,0.02,1.3
B material assign $M_LED $IDX; IDX=$((IDX+1))

# 7. Glass meeting room (SE): 4 glass walls + table + 10 chairs + big screen + whiteboard wall
# Glass partitions
B object add cube --name MR_GlassW   -l 2.0,-3.0,1.5  -s 0.03,2.0,1.5
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
B object add cube --name MR_GlassN   -l 4.25,-1.0,1.5 -s 2.25,0.03,1.5
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
# East and south sides use existing room walls but add frame
B object add cube --name MR_FrameE   -l 6.47,-3.0,1.5 -s 0.02,2.0,1.5
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cube --name MR_FrameS   -l 4.25,-4.97,1.5 -s 2.25,0.02,1.5
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
# Glass door
B object add cube --name MR_Door     -l 2.03,-1.5,1.05 -s 0.02,0.45,1.05
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
# Big conference table 2.4×1.0
B object add cube --name MR_Table    -l 4.25,-3.0,0.73 -s 1.2,0.5,0.03
B material assign $M_WOOD $IDX; IDX=$((IDX+1))
# 10 chairs (5 per side)
for i in 0 1 2 3 4; do
  y=$(python3 -c "print(-4.2 + $i * 0.6)")
  B object add cube --name "MR_ChairN_${i}" -l 3.2,${y},0.43 -s 0.22,0.22,0.03
  B material assign $M_CHAR $IDX; IDX=$((IDX+1))
  B object add cube --name "MR_ChairS_${i}" -l 5.3,${y},0.43 -s 0.22,0.22,0.03
  B material assign $M_CHAR $IDX; IDX=$((IDX+1))
done
# 75" big screen on east wall (inside meeting room)
B object add cube --name MR_BigScreen -l 6.4,-3.0,1.5  -s 0.02,0.7,0.45
B material assign $M_SCREEN $IDX; IDX=$((IDX+1))
# 4m whiteboard wall on south (inside meeting room)
B object add cube --name MR_Whiteboard -l 4.25,-4.93,1.5 -s 1.9,0.015,0.8
B material assign $M_WB $IDX; IDX=$((IDX+1))

# 8. 2 Phone booths (enclosed cubes, east side between server room and meeting room)
# Booth dimensions 1.2 × 1.2 × 2.5 m
B object add cube --name PhoneBooth1 -l 5.5,0.0,1.25  -s 0.6,0.6,1.25
B material assign $M_TEAL $IDX; IDX=$((IDX+1))
B object add cube --name Booth1_Door -l 4.89,0.0,1.1  -s 0.02,0.35,1.1
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
B object add cube --name Booth1_Desk -l 5.5,0.3,0.75  -s 0.5,0.2,0.02
B material assign $M_WOOD $IDX; IDX=$((IDX+1))
B object add cube --name PhoneBooth2 -l 5.5,1.5,1.25  -s 0.6,0.6,1.25
B material assign $M_TEAL $IDX; IDX=$((IDX+1))
B object add cube --name Booth2_Door -l 4.89,1.5,1.1  -s 0.02,0.35,1.1
B material assign $M_GLASS $IDX; IDX=$((IDX+1))
B object add cube --name Booth2_Desk -l 5.5,1.2,0.75  -s 0.5,0.2,0.02
B material assign $M_WOOD $IDX; IDX=$((IDX+1))

# 9. Kitchenette (NW corner)
B object add cube --name KitCounter  -l -5.5,4.5,0.45 -s 1.0,0.35,0.45
B material assign $M_WOOD $IDX; IDX=$((IDX+1))
B object add cube --name KitSink     -l -5.9,4.5,0.92 -s 0.2,0.15,0.02
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add cube --name KitFridge   -l -6.2,4.5,0.85 -s 0.3,0.3,0.85
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add cube --name KitCoffee   -l -5.3,4.5,1.05 -s 0.15,0.15,0.15
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cube --name KitMicro    -l -4.8,4.5,1.0  -s 0.2,0.18,0.12
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add cube --name KitUpCab    -l -5.5,4.9,2.3  -s 1.0,0.12,0.35
B material assign $M_WOOD $IDX; IDX=$((IDX+1))

# 10. Lounge + foosball (center-south area)
B object add cube --name Sofa1       -l 0.5,-2.0,0.35 -s 0.8,0.35,0.35
B material assign $M_TEAL $IDX; IDX=$((IDX+1))
B object add cube --name Sofa2       -l 2.3,-2.0,0.35 -s 0.8,0.35,0.35
B material assign $M_TEAL $IDX; IDX=$((IDX+1))
B object add cube --name CoffeeTable -l 1.4,-2.8,0.25 -s 0.4,0.25,0.03
B material assign $M_WOOD $IDX; IDX=$((IDX+1))
B object add cube --name Foosball    -l 1.4,-0.8,0.55 -s 0.7,0.35,0.1
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cylinder --name Foosball_leg1 -l 0.8,-0.8,0.225 -s 0.04,0.04,0.225
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add cylinder --name Foosball_leg2 -l 2.0,-0.8,0.225 -s 0.04,0.04,0.225
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add sphere --name BeanBag1  -l -0.3,-2.8,0.3  -s 0.3,0.3,0.3
B material assign $M_LIME $IDX; IDX=$((IDX+1))
B object add sphere --name BeanBag2  -l 2.9,-2.5,0.3   -s 0.3,0.3,0.3
B material assign $M_LIME $IDX; IDX=$((IDX+1))

# 11. Bathroom (small, NW west wall)
B object add cube --name BathWall1   -l -5.0,-0.5,1.2 -s 0.02,0.8,1.2
B material assign $M_WHITE $IDX; IDX=$((IDX+1))
B object add cube --name BathWall2   -l -5.75,0.3,1.2 -s 0.75,0.02,1.2
B material assign $M_WHITE $IDX; IDX=$((IDX+1))
B object add cube --name Toilet      -l -6.2,-0.3,0.25 -s 0.2,0.2,0.25
B material assign $M_WHITE $IDX; IDX=$((IDX+1))
B object add cube --name BathSink    -l -6.2,0.1,0.5  -s 0.2,0.15,0.05
B material assign $M_WHITE $IDX; IDX=$((IDX+1))

# 12. 5 large plants (cylinder pot + sphere foliage)
plant_pos=("-6.0,-2.5" "-6.0,2.5" "6.0,-2.5" "0.0,4.5" "-0.5,-4.0")
for i in 0 1 2 3 4; do
  pos="${plant_pos[$i]}"
  x=$(echo $pos | cut -d, -f1)
  y=$(echo $pos | cut -d, -f2)
  B object add cylinder --name "PlantPot_${i}" -l ${x},${y},0.3 -s 0.25,0.25,0.3
  B material assign $M_POT $IDX; IDX=$((IDX+1))
  B object add sphere --name "PlantFoliage_${i}" -l ${x},${y},1.0 -s 0.5,0.5,0.5
  B material assign $M_FOLIAGE $IDX; IDX=$((IDX+1))
done

# 13. Pendant lights + track lighting visuals
B object add cube --name CeilTrack1  -l -3.0,0.2,2.95  -s 3.0,0.05,0.02
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cube --name CeilTrack2  -l 3.0,0.2,2.95   -s 3.0,0.05,0.02
B material assign $M_CHAR $IDX; IDX=$((IDX+1))
B object add cylinder --name Pendant1 -l 1.4,-2.0,2.5  -s 0.08,0.08,0.15
B material assign $M_STEEL $IDX; IDX=$((IDX+1))
B object add cylinder --name Pendant2 -l 4.25,-3.0,2.4 -s 0.1,0.1,0.15
B material assign $M_STEEL $IDX; IDX=$((IDX+1))

# 14. Camera (isometric-ish angle showing interior)
B camera add --location=-7.5,-8.0,4.2 --rotation=70,0,-35 --active
B camera set 0 focal_length 20.0

# 15. Lights
B light add sun    -l 10,-10,8     -r 60,0,-45 -w 4.0 -c 1.0,0.97,0.9
B light add area   -l -3.0,0.5,2.9 -r 0,0,0    -w 200 -c 1.0,0.95,0.85
B light add area   -l 3.0,0.5,2.9  -r 0,0,0    -w 200 -c 1.0,0.95,0.85
B light add point  -l 4.8,3.8,2.0  -r 0,0,0    -w 50  -c 0.3,0.6,1.0
B light add point  -l -4.5,-4.5,2.5 -r 0,0,0   -w 40  -c 0.8,0.95,0.4

# 16. Render settings + render
B render settings --engine EEVEE --samples 64 --resolution-x 1600 --resolution-y 1000
B render execute render.png --overwrite

echo "===OBJ_COUNT==="
python3 -c "import json; p=json.load(open('room.json')); print('OBJECTS:', len(p['objects']))"

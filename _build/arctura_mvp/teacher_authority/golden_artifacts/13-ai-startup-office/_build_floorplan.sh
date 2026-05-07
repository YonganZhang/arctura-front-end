#!/usr/bin/env bash
# Floor plan: 13m × 10m room, 1m = 80px, margin 150/50.
# Canvas w=1340 h=950. Room top-left (150,50), bottom-right (1190,850).

set -e
cd /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office

I() { cli-anything-inkscape --project floorplan.inkscape-cli.json "$@"; }

# New document
cli-anything-inkscape document new --width 1340 --height 950 --background "#FFFFFF" -o floorplan.inkscape-cli.json

# Helper: add rect with fill/stroke
rect() { I shape add-rect --x "$1" --y "$2" -w "$3" -h "$4" --style "$5"; }
circ() { I shape add-circle --cx "$1" --cy "$2" --r "$3" --style "$4"; }
line() { I shape add-line --x1 "$1" --y1 "$2" --x2 "$3" --y2 "$4" --style "$5"; }
txt()  { I text add --x "$1" --y "$2" --text "$3" --font-size "$4" --fill "$5" --text-anchor "$6" --font-weight "${7:-normal}"; }

# Title
txt 670 35 "BUBBLE PLAN | Stack Lab (AI Startup Office) 13.0m × 10.0m (130 sqm)" 22 "#2A2A2C" middle bold

# Room outline
rect 150 50 1040 800 "fill:#F5F3EE;stroke:#2A2A2C;stroke-width:3"

# North arrow
txt 670 70 "N ↑" 14 "#2A2A2C" middle

# --- Entry + LOGO (SW) ---
rect 150 690 280 160 "fill:#F0EDE5;stroke:#8B6F4E;stroke-width:1.5"
txt 290 780 "入口 + LOGO" 14 "#2A2A2C" middle bold
rect 190 840 240 8 "fill:#2A2A2C"
rect 210 842 200 4 "fill:#A8C947"
rect 310 770 120 70 "fill:#8B6F4E;stroke:#2A2A2C;stroke-width:1"
txt 370 810 "接待台" 11 "#F0EDE5" middle
rect 190 770 120 40 "fill:#2E5454"
txt 250 795 "长凳" 10 "#F0EDE5" middle

# --- Open desks zone ---
rect 150 210 640 400 "fill:#FBF9F3;stroke:#2E5454;stroke-width:1.5"
txt 470 240 "开放工位 · 10 位 × 双屏" 14 "#2E5454" middle bold

# 10 desks
for i in 0 1 2 3 4; do
  bx=$(python3 -c "print(-5 + $i * 1.4)")
  sx=$(python3 -c "print(round(150 + ($bx + 6.5) * 80))")
  x1=$((sx-48))
  # Row 1 (south)
  rect $x1 550 96 56 "fill:#8B6F4E;stroke:#2A2A2C;stroke-width:1"
  circ $sx 520 12 "fill:#2A2A2C"
  # Row 2 (north)
  rect $x1 288 96 56 "fill:#8B6F4E;stroke:#2A2A2C;stroke-width:1"
  circ $sx 358 12 "fill:#2A2A2C"
  # Dual screens (small rects on desk)
  rect $((sx-40)) 548 32 4 "fill:#0B0D14"
  rect $((sx+8))  548 32 4 "fill:#0B0D14"
  rect $((sx-40)) 342 32 4 "fill:#0B0D14"
  rect $((sx+8))  342 32 4 "fill:#0B0D14"
done
rect 180 425 580 8 "fill:#2E5454"
txt 470 420 "工位隔板" 9 "#F0EDE5" middle

# --- GPU server room (NE) ---
rect 910 50 280 240 "fill:#E8EAE4;stroke:#2A2A2C;stroke-width:2"
txt 1050 75 "GPU 机柜服务器室" 13 "#2A2A2C" middle bold
rect 970 120 48 80 "fill:#2A2A2C"
rect 1046 120 48 80 "fill:#2A2A2C"
rect 1122 120 48 80 "fill:#2A2A2C"
rect 970 116 48 4 "fill:#3498F4"
rect 1046 116 48 4 "fill:#3498F4"
rect 1122 116 48 4 "fill:#3498F4"
txt 1050 250 "3 × 42U Rack · 蓝 LED" 10 "#2A2A2C" middle

# --- Glass meeting room (SE) ---
rect 830 530 360 320 "fill:#F0F5F5;stroke:#2E5454;stroke-width:2"
txt 1010 560 "玻璃会议室 · 10 人" 13 "#2E5454" middle bold
rect 930 660 192 80 "fill:#8B6F4E;stroke:#2A2A2C;stroke-width:1"
for i in 0 1 2 3 4; do
  cx=$(python3 -c "print(round(950 + $i * 38))")
  circ $cx 640 10 "fill:#2A2A2C"
  circ $cx 760 10 "fill:#2A2A2C"
done
rect 1180 680 10 80 "fill:#0B0D14"
txt 1185 675 "75″" 9 "#2A2A2C" end
rect 850 835 320 8 "fill:#F5F5F0;stroke:#2A2A2C;stroke-width:1"
txt 1010 828 "4m 白板墙" 10 "#2A2A2C" middle

# --- Phone booths (E mid) ---
rect 1090 370 96 96 "fill:#2E5454;stroke:#2A2A2C;stroke-width:1"
txt 1138 420 "电话亭 1" 10 "#F0EDE5" middle
rect 1090 250 96 96 "fill:#2E5454;stroke:#2A2A2C;stroke-width:1"
txt 1138 302 "电话亭 2" 10 "#F0EDE5" middle

# --- Kitchenette (NW) ---
rect 150 50 160 160 "fill:#F5F0E6;stroke:#8B6F4E;stroke-width:1.5"
txt 230 80 "茶水间" 13 "#8B6F4E" middle bold
rect 158 130 140 40 "fill:#8B6F4E"
rect 170 140 30 20 "fill:#B5B0A8"
rect 210 140 30 20 "fill:#2A2A2C"
rect 250 140 40 20 "fill:#B5B0A8"
txt 230 190 "吧台 · 水槽 · 冰箱" 9 "#2A2A2C" middle

# --- Lounge + foosball ---
rect 630 450 280 240 "fill:#F5F3EE;stroke:#A8C947;stroke-width:1.5"
txt 770 475 "休闲沙发 + 桌足球" 12 "#2A2A2C" middle bold
rect 660 580 80 50 "fill:#2E5454"
rect 800 580 80 50 "fill:#2E5454"
circ 770 660 18 "fill:#8B6F4E"
rect 700 490 140 60 "fill:#2A2A2C"
txt 770 525 "Foosball" 10 "#F0EDE5" middle
circ 640 670 18 "fill:#A8C947"
circ 900 640 18 "fill:#A8C947"

# --- Bathroom ---
rect 150 450 160 130 "fill:#EEEFF1;stroke:#2A2A2C;stroke-width:1.5"
txt 230 475 "WC" 12 "#2A2A2C" middle bold
rect 170 490 40 40 "fill:#FFFFFF;stroke:#2A2A2C;stroke-width:1"
rect 230 500 60 20 "fill:#FFFFFF;stroke:#2A2A2C;stroke-width:1"

# --- 5 plants (foliage green circles) ---
circ 190 650 16 "fill:#3F6B3C"
circ 190 250 16 "fill:#3F6B3C"
circ 890 400 16 "fill:#3F6B3C"
circ 670 90 16 "fill:#3F6B3C"
circ 620 790 16 "fill:#3F6B3C"

# Circulation dashed line
line 430 770 910 770 "stroke:#A8C947;stroke-width:2;stroke-dasharray:8,4;fill:none"
line 670 770 670 400 "stroke:#A8C947;stroke-width:2;stroke-dasharray:8,4;fill:none"

# Footer notes
txt 1250 900 "1m = 80px · Scale 1:80" 10 "#8B6F4E" end
txt 150 900 "致敬业主 · Stack Lab · made with love" 11 "#2E5454" start
txt 150 920 "9 zones · 10 desks (20 screens) · 3 GPU racks · 10-person meeting · 2 phone booths · 5 plants" 10 "#2A2A2C" start

# Exports
mkdir -p exports
I export svg floorplan.svg --overwrite
I export png floorplan.png --overwrite
I export dxf exports/floorplan.dxf --overwrite

echo "===FLOORPLAN DONE==="

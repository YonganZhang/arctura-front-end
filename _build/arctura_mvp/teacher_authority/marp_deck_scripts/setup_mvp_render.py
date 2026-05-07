#!/usr/bin/env python3
"""For each MVP folder: read brief.json → write _render_multi.py with proper room dims."""
import json, sys
from pathlib import Path

ROOT = Path('/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp')
TAIL_PATH = Path(__file__).parent / '_render_multi_tail.py'
TAIL = TAIL_PATH.read_text()

MVPS = sys.argv[1:] if len(sys.argv) > 1 else None

for mvp_dir in sorted(ROOT.iterdir()):
    if not mvp_dir.is_dir(): continue
    if MVPS and mvp_dir.name not in MVPS: continue
    brief_p = mvp_dir / 'brief.json'
    src_p = mvp_dir / '_render_script.py'
    if not (brief_p.exists() and src_p.exists()):
        print(f'[SKIP] {mvp_dir.name} (no brief/script)')
        continue
    brief = json.loads(brief_p.read_text())
    dim = brief.get('space', {}).get('dimensions_m', {})
    L = dim.get('length', 10.0)
    W = dim.get('width', 10.0)
    H = dim.get('height', 3.0)

    # Find "# ── Cameras" line in source
    src_lines = src_p.read_text().splitlines()
    cut = next((i for i, ln in enumerate(src_lines) if ln.startswith('# ── Cameras')), None)
    if cut is None:
        print(f'[SKIP] {mvp_dir.name}: no Cameras marker')
        continue
    head = '\n'.join(src_lines[:cut]) + '\n'

    render_dir = mvp_dir / 'renders'
    render_dir.mkdir(exist_ok=True)

    tail = (TAIL
            .replace('__ROOM_LEN__', str(L))
            .replace('__ROOM_WID__', str(W))
            .replace('__ROOM_HT__', str(H))
            .replace('__RENDER_DIR__', str(render_dir)))

    out = mvp_dir / '_render_multi.py'
    out.write_text(head + tail)
    print(f'[OK] {mvp_dir.name}: {L}×{W}×{H} m')

print('done.')

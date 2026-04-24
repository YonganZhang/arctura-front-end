#!/usr/bin/env python3
"""
build_mvp_data.py — 扫 StartUP-Building 的 41 个 MVP 产数据 JSON 给前端用

Input:
  - $SB_ROOT/studio-demo/mvp/*/  (室内 25 个)
  - $SB_ROOT/studio-demo/arch-mvp/*/  (建筑 17 个)
  - $SB_ROOT/studio-demo/ALL-MVPS-ENERGY-BOQ.json (聚合能耗/合规)

Output:
  - Arctura-Front-end/data/mvps-index.json  (gallery 摘要)
  - Arctura-Front-end/data/mvps/<slug>.json  (每 MVP 完整数据 · Project Space 用)

Usage:
  source env-linux.sh  # 设 $SB_ROOT
  $PY _build/build_mvp_data.py
"""

import json
import os
import sys
from pathlib import Path

# Phase 9.4 · 纯扫盘逻辑已抽到 arctura_mvp.materializer · 这里只做 CLI + 批量 loop
sys.path.insert(0, str(Path(__file__).resolve().parent))
from arctura_mvp.materializer import (  # noqa: E402
    build_mvp_record as _build_mvp_record,
    safe_read_json,
)

SB_ROOT = Path(os.environ.get("SB_ROOT", "/root/projects/公司项目/Building-CLI-Anything/StartUP-Building"))
FE_ROOT = Path(__file__).resolve().parents[1]  # Arctura-Front-end/
OUT_DATA = FE_ROOT / "data"
OUT_MVPS = OUT_DATA / "mvps"


def build_mvp_record(mvp_dir: Path, mvp_type: str, agg: dict) -> tuple[dict, dict]:
    """Shim · 老 CLI 接口 · 转发给 materializer（Phase 9.4）"""
    return _build_mvp_record(mvp_dir, mvp_type, agg, FE_ROOT)



def main():
    if not SB_ROOT.exists():
        print(f"❌ SB_ROOT 不存在: {SB_ROOT}")
        sys.exit(1)

    # 读聚合数据
    agg_path = SB_ROOT / "studio-demo" / "ALL-MVPS-ENERGY-BOQ.json"
    agg_data = safe_read_json(agg_path)
    agg_results = agg_data.get("results", []) or []
    agg_by_slug = {r.get("slug"): r for r in agg_results if r.get("slug")}
    print(f"📊 聚合数据: {len(agg_by_slug)} 个 MVP")

    # 扫 mvp + arch-mvp
    OUT_MVPS.mkdir(parents=True, exist_ok=True)
    OUT_DATA.mkdir(parents=True, exist_ok=True)

    index = []
    complete_count = 0

    for base, mvp_type in [("mvp", "P1-interior"), ("arch-mvp", "P2-architecture")]:
        base_dir = SB_ROOT / "studio-demo" / base
        if not base_dir.is_dir():
            continue
        for mvp_dir in sorted(base_dir.iterdir()):
            if not mvp_dir.is_dir() or mvp_dir.name.startswith("_"):
                continue
            slug = mvp_dir.name
            agg = agg_by_slug.get(slug, {})
            try:
                index_entry, full_data = build_mvp_record(mvp_dir, mvp_type, agg)
                index.append(index_entry)
                if index_entry["complete"]:
                    complete_count += 1
                (OUT_MVPS / f"{slug}.json").write_text(
                    json.dumps(full_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"  {'✅' if index_entry['complete'] else '⚠️'} {slug:<40} {index_entry['cat']:<12} EUI={index_entry['eui']} cost={index_entry['cost_per_m2']}")
            except Exception as e:
                print(f"  ❌ {slug}: {e}")
                import traceback
                traceback.print_exc()

    # 按 complete 降序 + slug 升序
    index.sort(key=lambda x: (not x["complete"], x["slug"]))
    (OUT_DATA / "mvps-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n📈 总计: {len(index)} MVP · 完整 {complete_count} · 写入 data/mvps-index.json + data/mvps/*.json")

    # 自动 schema 校验 · 任何字段缺失 exit 1
    print()
    import subprocess
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "validate.py"), "--quiet"],
        capture_output=True, text=True,
    )
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\n❌ Schema 校验失败 · build 输出的 JSON 不符合 schema · 请检查 build_mvp_data.py 逻辑")
        sys.exit(1)


if __name__ == "__main__":
    main()

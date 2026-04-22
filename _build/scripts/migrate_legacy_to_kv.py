#!/usr/bin/env python3
"""把 data/mvps/*.json 的 42 个老 MVP 迁入 Upstash KV

幂等：守护 key `migration:legacy:v1` 已存在 → skip。删该 key 可重跑（ZADD 自动去重）。

用法：
  source ~/.arctura-env
  python3 _build/scripts/migrate_legacy_to_kv.py [--force]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _build.arctura_mvp.store import kv
from _build.arctura_mvp._core import put_project
from _build.arctura_mvp.types import Project, utc_now


GUARD_KEY = "migration:legacy:v1"


def load_legacy_mvps() -> list[dict]:
    data_dir = ROOT / "data" / "mvps"
    files = sorted(data_dir.glob("*.json"))
    mvps = []
    for fp in files:
        try:
            mvp = json.loads(fp.read_text())
            mvps.append(mvp)
        except Exception as e:
            print(f"⚠ skip {fp.name}: {e}", file=sys.stderr)
    return mvps


def mvp_to_project(mvp: dict) -> Project:
    """映射老 MVP JSON → Project dataclass"""
    proj = mvp.get("project", {})
    return Project(
        slug=mvp["slug"],
        state="live",                          # 已生成 · 算 live
        version=1,
        visibility="public",                   # legacy 默认公开
        owner="legacy",
        display_name=proj.get("zh") or proj.get("name") or mvp["slug"],
        brief=None,                             # legacy 没 brief schema · 以后重跑生成
        brief_schema_version="legacy",
        tier=None,                              # legacy 未分档
        variant_count=3 if (mvp.get("variants", {}).get("list") or []) else 1,
        render_engine=None,
        scene=mvp.get("scene"),
        scene_schema_version="v1",
        artifacts={
            "produced": ["brief", "scene", "renders"] if mvp.get("renders") else ["brief"],
            "skipped": [],
            "errors": [],
            "partial": False,
            "timing_ms": {},
            "urls": {
                "mvp_page": f"https://arctura-front-end.vercel.app/project/{mvp['slug']}",
                "bundle": (next((d.get("href") for d in mvp.get("downloads", []) if d.get("ext") == "zip"), None)
                           or f"/assets/mvps/{mvp['slug']}/bundle.zip"),
                "hero_img": mvp.get("hero_img"),
                "floorplan": mvp.get("floorplan"),
                "moodboard": mvp.get("moodboard"),
            },
        },
        pending_count=0,
        last_save_ref=None,
        created_at=utc_now(),
        updated_at=utc_now(),
        _pii_fields=[],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="忽略守护 key 强制重跑")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写")
    args = ap.parse_args()

    if not args.force and kv.exists(GUARD_KEY):
        print(f"✓ 已迁移（守护 key {GUARD_KEY} 存在）· 跳过。--force 强制重跑")
        return

    mvps = load_legacy_mvps()
    print(f"▸ 扫到 {len(mvps)} 个 MVP JSON")

    migrated = 0
    failed = []
    for i, mvp in enumerate(mvps, 1):
        slug = mvp["slug"]
        try:
            p = mvp_to_project(mvp)
            if args.dry_run:
                print(f"  [dry] {i}/{len(mvps)} {slug} · hero={p.artifacts['urls'].get('hero_img')}")
            else:
                put_project(p)
                if i % 10 == 0 or i == len(mvps):
                    print(f"  {i}/{len(mvps)} done (latest: {slug})")
            migrated += 1
        except Exception as e:
            failed.append((slug, str(e)))
            print(f"  ✗ {slug}: {e}", file=sys.stderr)

    if not args.dry_run:
        kv.set(GUARD_KEY, utc_now(), ex=None)  # 不 TTL · persist 通过去掉 EX
        print(f"\n✓ 迁移完成 · {migrated} 成功 · {len(failed)} 失败 · 守护 key 已设")
        print(f"  ZCARD projects:index = {kv.zcard('projects:index')}")
        if failed:
            print("  失败清单:", failed)
    else:
        print(f"\n[dry-run] 将迁移 {migrated} 个 · 未写")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
validate.py — 校验所有 MVP JSON / variant JSON / data.js 是否符合 schema
跑在 build 末尾（build_mvp_data.py · build_variants.py）· 任何字段缺失/类型错 exit 1

Usage:
  python3 _build/validate.py              # 全部校验
  python3 _build/validate.py --quiet      # 只打错误
  python3 _build/validate.py --skip-js    # 跳过 data.js（它是 JS 不是 JSON）
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("❌ 需要 jsonschema: pip install --user jsonschema")
    sys.exit(2)

FE_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate_one(obj: dict, schema: dict, source: str) -> list[str]:
    """用 iter_errors 拿所有错 · 返回错误字符串列表"""
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path))
    return [f"  {source}:{'/'.join(str(p) for p in e.absolute_path) or '(root)'}  {e.message[:120]}"
            for e in errors]


def extract_zen_data_from_js(js_path: Path) -> dict | None:
    """从 data.js 抽 window.ZEN_DATA 对象 · 返回 dict 或 None"""
    text = js_path.read_text(encoding="utf-8")
    # 找 window.ZEN_DATA = {...};  取到匹配的大括号
    m = re.search(r"window\.ZEN_DATA\s*=\s*(\{)", text)
    if not m:
        return None
    start = m.end() - 1  # 指向 {
    depth = 0
    in_str = False
    str_ch = None
    i = start
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == str_ch:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_ch = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = text[start:i+1]
                    # 简单 JS → JSON：去尾逗号 · 把 key 用引号包
                    # 这里 data.js 比较规整，直接 eval 安全点
                    # 用 json5 / ast.literal_eval 都不行 · 走 subprocess node eval 最稳
                    return _js_to_dict_via_node(body)
        i += 1
    return None


def _js_to_dict_via_node(js_obj_literal: str) -> dict | None:
    """Node 一行跑 eval · 打印 JSON"""
    import subprocess
    try:
        script = f"console.log(JSON.stringify({js_obj_literal}))"
        r = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--skip-js", action="store_true", help="跳过 data.js")
    args = ap.parse_args()

    mvp_schema = load_schema("mvp.schema.json")
    variant_schema = load_schema("variant.schema.json")

    all_errors: list[tuple[str, list[str]]] = []
    counts = {"mvp": 0, "variant": 0, "data_js": 0}

    # 1. 全部 MVP JSON
    mvp_files = sorted((FE_ROOT / "data" / "mvps").glob("*.json"))
    for p in mvp_files:
        if p.name == "mvps-index.json":
            continue  # 索引文件不走此 schema
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            all_errors.append((str(p), [f"  JSON parse error: {e}"]))
            continue
        errs = validate_one(obj, mvp_schema, p.name)
        counts["mvp"] += 1
        if errs:
            all_errors.append((str(p), errs))
        elif not args.quiet:
            print(f"✓ MVP     {p.relative_to(FE_ROOT)}")

    # 2. 全部 variant JSON
    variant_files = sorted((FE_ROOT / "data" / "mvps").rglob("variants/*.json"))
    for p in variant_files:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            all_errors.append((str(p), [f"  JSON parse error: {e}"]))
            continue
        errs = validate_one(obj, variant_schema, p.name)
        counts["variant"] += 1
        if errs:
            all_errors.append((str(p), errs))
        elif not args.quiet:
            print(f"✓ variant {p.relative_to(FE_ROOT)}")

    # 3. data.js 默认（从 JS 里抽 ZEN_DATA 走 mvp schema 的一个宽松版）
    if not args.skip_js:
        data_js = FE_ROOT / "project-space" / "data.js"
        if data_js.exists():
            zen = extract_zen_data_from_js(data_js)
            if zen is None:
                all_errors.append((str(data_js), ["  Cannot extract window.ZEN_DATA from JS"]))
            else:
                # data.js 用 mvp_schema 但只要关键核心字段（不要 require variants/decks/downloads 等）
                loose_schema = {
                    **mvp_schema,
                    "required": ["slug", "cat", "project", "editable", "derived", "pricing", "compliance", "energy"],
                }
                errs = validate_one(zen, loose_schema, "data.js")
                counts["data_js"] += 1
                if errs:
                    all_errors.append((str(data_js), errs))
                elif not args.quiet:
                    print(f"✓ data.js {data_js.relative_to(FE_ROOT)} (loose schema)")

    # 汇总
    print()
    total = counts["mvp"] + counts["variant"] + counts["data_js"]
    print(f"📊 校验 {total} 份 · MVP {counts['mvp']} · variant {counts['variant']} · data.js {counts['data_js']}")

    if all_errors:
        print(f"\n❌ {len(all_errors)} 份不过校验：\n")
        for src, errs in all_errors:
            print(f"  {Path(src).relative_to(FE_ROOT)}")
            for e in errs[:5]:
                print(e)
            if len(errs) > 5:
                print(f"  ... 还有 {len(errs)-5} 条")
        sys.exit(1)

    print("✅ 全部符合 schema")
    sys.exit(0)


if __name__ == "__main__":
    main()

"""JSON 版本化工具 — 备份/回滚/对比 brief.json 或 room.json。

用法:
    # 备份当前文件（自动递增版本号）
    python brief_version.py backup <mvp-dir> [--target brief|room]

    # 查看版本历史
    python brief_version.py list <mvp-dir> [--target room]

    # 回滚到指定版本
    python brief_version.py restore <mvp-dir> v2 [--target room]

    # 对比两个版本差异（v1 vs v2，或 v1 vs current）
    python brief_version.py diff <mvp-dir> v1 v2 [--target room]
    python brief_version.py diff <mvp-dir> v1 current [--target room]

    --target 默认为 brief（管理 brief.json），传 room 则管理 room.json。

示例:
    PY=/opt/anaconda3/envs/mini-2025/bin/python
    $PY playbooks/scripts/brief_version.py backup studio-demo/mvp/19-industrial-living-room
    $PY playbooks/scripts/brief_version.py backup studio-demo/mvp/14-central-japanese-coffee-bakery --target room
    $PY playbooks/scripts/brief_version.py list studio-demo/mvp/14-central-japanese-coffee-bakery --target room
    $PY playbooks/scripts/brief_version.py restore studio-demo/mvp/14-central-japanese-coffee-bakery v1 --target room
    $PY playbooks/scripts/brief_version.py diff studio-demo/mvp/14-central-japanese-coffee-bakery v1 v2 --target room
"""

import json
import re
import shutil
import sys
from pathlib import Path


def _target_path(mvp_dir: Path, target: str) -> Path:
    return mvp_dir / f"{target}.json"


def _version_files(mvp_dir: Path, target: str = "brief") -> list[tuple[int, Path]]:
    """Return sorted list of (version_number, path) for <target>-vN.json files."""
    pattern = re.compile(rf"^{re.escape(target)}-v(\d+)\.json$")
    versions = []
    for f in mvp_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            versions.append((int(m.group(1)), f))
    versions.sort(key=lambda x: x[0])
    return versions


def _next_version(mvp_dir: Path, target: str = "brief") -> int:
    versions = _version_files(mvp_dir, target)
    return versions[-1][0] + 1 if versions else 1


def cmd_backup(mvp_dir: Path, target: str = "brief") -> None:
    src = _target_path(mvp_dir, target)
    if not src.exists():
        print(f"ERROR: {src} not found")
        sys.exit(1)

    ver = _next_version(mvp_dir, target)
    dest = mvp_dir / f"{target}-v{ver}.json"
    shutil.copy2(src, dest)
    print(f"OK: {src.name} -> {dest.name} (version {ver})")


def cmd_list(mvp_dir: Path, target: str = "brief") -> None:
    versions = _version_files(mvp_dir, target)
    src = _target_path(mvp_dir, target)

    if not versions and not src.exists():
        print(f"No {target}.json found.")
        return

    if src.exists():
        print(f"  current  {target}.json  ({src.stat().st_size:,} bytes)")
    for ver, path in versions:
        print(f"  v{ver:<6} {path.name}  ({path.stat().st_size:,} bytes)")

    print(f"\nTotal: {len(versions)} backup(s)")


def cmd_restore(mvp_dir: Path, version: str, target: str = "brief") -> None:
    try:
        ver_num = int(version.lstrip("v"))
    except ValueError:
        print(f"ERROR: Invalid version '{version}'. Use format: v1, v2, v3...")
        sys.exit(1)
    src = mvp_dir / f"{target}-v{ver_num}.json"
    dst = _target_path(mvp_dir, target)

    if not src.exists():
        print(f"ERROR: {src} not found")
        sys.exit(1)

    # Backup current before overwriting
    if dst.exists():
        backup_ver = _next_version(mvp_dir, target)
        backup_dest = mvp_dir / f"{target}-v{backup_ver}.json"
        shutil.copy2(dst, backup_dest)
        print(f"Backed up current as {backup_dest.name} (v{backup_ver})")

    shutil.copy2(src, dst)
    print(f"OK: Restored {target}.json from v{ver_num}")


def cmd_diff(mvp_dir: Path, ver_a: str, ver_b: str, target: str = "brief") -> None:
    """Show field-level diff between two versions (or 'current')."""

    def _load(label: str) -> dict:
        if label == "current":
            p = _target_path(mvp_dir, target)
        else:
            try:
                n = int(label.lstrip("v"))
            except ValueError:
                print(f"ERROR: Invalid version '{label}'. Use v1, v2, ... or 'current'")
                sys.exit(1)
            p = mvp_dir / f"{target}-v{n}.json"
        if not p.exists():
            print(f"ERROR: {p} not found")
            sys.exit(1)
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            print(f"ERROR: {p} is not a valid JSON object")
            sys.exit(1)
        return data

    a = _load(ver_a)
    b = _load(ver_b)

    diffs = _dict_diff(a, b, prefix="")
    if not diffs:
        print(f"No differences between {ver_a} and {ver_b}.")
        return

    print(f"Diff: {ver_a} -> {ver_b}\n")
    for path, (old, new) in sorted(diffs.items()):
        if old is None:
            print(f"  + {path}: {_short(new)}")
        elif new is None:
            print(f"  - {path}: {_short(old)}")
        else:
            print(f"  ~ {path}: {_short(old)} -> {_short(new)}")

    print(f"\n{len(diffs)} field(s) changed.")


_MISSING = object()


def _dict_diff(a: dict, b: dict, prefix: str) -> dict:
    """Recursively compare two dicts, return {dotted.path: (old, new)}."""
    diffs = {}
    all_keys = set(list(a.keys()) + list(b.keys()))
    for k in all_keys:
        path = f"{prefix}.{k}" if prefix else k
        va = a.get(k, _MISSING)
        vb = b.get(k, _MISSING)
        if va is _MISSING:
            diffs[path] = (None, vb)
        elif vb is _MISSING:
            diffs[path] = (va, None)
        elif va == vb:
            continue
        elif isinstance(va, dict) and isinstance(vb, dict):
            diffs.update(_dict_diff(va, vb, path))
        else:
            diffs[path] = (va, vb)
    return diffs


def _short(val, max_len: int = 60) -> str:
    s = json.dumps(val, ensure_ascii=False)
    return s if len(s) <= max_len else s[:max_len - 3] + "..."


def _parse_target(argv: list[str]) -> tuple[list[str], str]:
    """Extract --target <name> from argv, return (remaining_argv, target)."""
    target = "brief"
    remaining = []
    i = 0
    while i < len(argv):
        if argv[i] == "--target" and i + 1 < len(argv):
            target = argv[i + 1]
            i += 2
        else:
            remaining.append(argv[i])
            i += 1
    return remaining, target


def main():
    args, target = _parse_target(sys.argv[1:])

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]
    mvp_dir = Path(args[1]).resolve()

    if not mvp_dir.is_dir():
        print(f"ERROR: {mvp_dir} is not a directory")
        sys.exit(1)

    if cmd == "backup":
        cmd_backup(mvp_dir, target)
    elif cmd == "list":
        cmd_list(mvp_dir, target)
    elif cmd == "restore":
        if len(args) < 3:
            print("Usage: brief_version.py restore <mvp-dir> <vN> [--target room]")
            sys.exit(1)
        cmd_restore(mvp_dir, args[2], target)
    elif cmd == "diff":
        if len(args) < 4:
            print("Usage: brief_version.py diff <mvp-dir> <v1> <v2|current> [--target room]")
            sys.exit(1)
        cmd_diff(mvp_dir, args[2], args[3], target)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

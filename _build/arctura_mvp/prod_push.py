"""prod_push · Phase 9.7 Fix E · worker 跑完自动推 GitHub + Vercel（2026-04-25）

Context:
  Phase 9.5 Fix A 让前端 `fetch /data/mvps/<slug>.json` 404 时降级 KV 读 fe_payload ·
  但 fe_payload 里 renders / glb / pptx 等资产路径是 `/assets/mvps/<slug>/*` ·
  这些文件只在 worker 本机 · 没推到 GitHub → Vercel CDN 404 → 用户看到破图。

  Fix A 只解了 JSON 能读 · 不解资产能拿。要想用户"新建 MVP 生成完立刻看全内容" ·
  必须让 worker 自己把资产推到 prod · 这就是 Fix E。

Flow:
  1. 从 sb_dir (StartUP-Building/studio-demo/mvp/<slug>/) 拷资产到 REPO_ROOT/assets/mvps/<slug>/
     - slug.glb / exports/*.{obj,fbx,ifc,mtl} / decks/*.{pptx,pdf,md}
     - energy/*.{md,csv} / CLIENT-README.md / moodboard.png / floorplan.png
     - renders/ 和 bundle.zip LIGHT 已经直接写到 fe_root · 不用拷
  2. git add + commit + push（HTTPS · 用 gh credential helper 或 GITHUB_TOKEN）
  3. 若 Vercel git integration 不 auto deploy · fallback 跑 `vercel --prod`（bg · 不阻塞 worker）

Safety:
  - flock 防并发 worker 同时 git push 冲突
  - rebase-then-push 重试 3 次（上游有新 commit 时）
  - 任何 fail 只 log 不 raise · 不 block worker 生命周期（KV fallback 是第二保障）
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from .paths import REPO_ROOT


def _run(cmd: list[str], cwd: Optional[Path] = None, timeout: int = 30, env_extra: dict = None) -> tuple[int, str, str]:
    """subprocess wrap · 返 (rc, stdout, stderr) · 不抛"""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout({timeout}s)"
    except FileNotFoundError as e:
        return 127, "", f"cmd not found: {e}"


def _copy_artifact_files(sb_dir: Path, fe_assets: Path, slug: str) -> list[str]:
    """从 sb_dir 拷资产到 fe_root/assets/mvps/<slug>/ · 返拷成功路径清单"""
    fe_assets.mkdir(parents=True, exist_ok=True)
    (fe_assets / "exports").mkdir(exist_ok=True)
    (fe_assets / "decks").mkdir(exist_ok=True)
    (fe_assets / "energy").mkdir(exist_ok=True)

    copied = []
    # GLB · model-viewer 硬依赖 · 必拷
    src_glb = sb_dir / "exports" / f"{slug}.glb"
    if src_glb.exists():
        shutil.copy2(src_glb, fe_assets / f"{slug}.glb")
        copied.append(f"{slug}.glb")
    # 其他 exports（Downloads tab）
    for ext in ("obj", "mtl", "fbx", "ifc"):
        src = sb_dir / "exports" / f"{slug}.{ext}"
        if src.exists():
            shutil.copy2(src, fe_assets / "exports" / f"{slug}.{ext}")
            copied.append(f"exports/{slug}.{ext}")
    # decks
    for name in ("deck-client.pptx", "deck-client.pdf", "deck-client.md"):
        src = sb_dir / "decks" / name
        if src.exists():
            shutil.copy2(src, fe_assets / "decks" / name)
            copied.append(f"decks/{name}")
    # energy · BOQ + compliance
    for name in ("boq-HK.md", "boq-HK.csv", "compliance-HK.md"):
        src = sb_dir / "energy" / name
        if src.exists():
            shutil.copy2(src, fe_assets / "energy" / name)
            copied.append(f"energy/{name}")
    # CLIENT-README + moodboard + floorplan
    for name in ("CLIENT-README.md", "moodboard.png", "floorplan.png"):
        src = sb_dir / name
        if src.exists():
            shutil.copy2(src, fe_assets / name)
            copied.append(name)
    return copied


def _git_push(slug: str, commit_msg: str) -> tuple[bool, Optional[str], Optional[str]]:
    """git add + commit + push · 返 (ok, sha, error)"""
    # 1. add 白名单路径 · 避免误 add 本机别的脏修改
    paths = [
        f"data/mvps/{slug}.json",
        f"assets/mvps/{slug}/",
    ]
    rc, _, err = _run(["git", "add", "--", *paths], cwd=REPO_ROOT)
    if rc != 0:
        return False, None, f"git add: {err[:200]}"

    # 2. 如没有待 commit · 说明本次什么也没新变（脚本重入）· 视为成功
    rc, out, _ = _run(["git", "diff", "--cached", "--name-only"], cwd=REPO_ROOT)
    if rc == 0 and not out.strip():
        return True, None, None

    # 3. commit
    rc, _, err = _run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, timeout=20)
    if rc != 0:
        return False, None, f"git commit: {err[:200]}"
    rc, sha, _ = _run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    sha = sha.strip() if rc == 0 else None

    # 4. push · 失败 rebase-then-push 重试 3 次
    for attempt in range(3):
        rc, _, err = _run(["git", "push", "origin", "main"], cwd=REPO_ROOT, timeout=60)
        if rc == 0:
            return True, sha, None
        # non-fast-forward → pull --rebase 再推
        if "non-fast-forward" in err.lower() or "fetch first" in err.lower():
            _run(["git", "pull", "--rebase", "origin", "main"], cwd=REPO_ROOT, timeout=30)
            continue
        # 其他错 · 直接停
        return False, sha, f"git push (attempt {attempt+1}): {err[:200]}"
    return False, sha, "git push: 3 attempts all failed"


def _vercel_deploy_bg() -> None:
    """后台跑 vercel --prod · 不阻塞 worker · 失败仅 log

    Vercel git integration 断时用（Phase 9.4 起的状态）· 集成修好后此步多余但无害。
    """
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        # 从 share-docx helper 拿
        helper = Path(os.environ.get("HOME", "/root")) / ".claude" / "skills" / "share-docx" / "scripts" / "get-credential.sh"
        if helper.exists():
            rc, tok, _ = _run([str(helper), "VERCEL_TOKEN"], timeout=10)
            if rc == 0 and tok.strip().startswith("vcp_"):
                token = tok.strip()
    if not token:
        print("[prod_push] no VERCEL_TOKEN · skip Vercel deploy", flush=True)
        return

    # 跑 vercel · 不等结果 · background
    log_path = Path("/tmp") / f"arctura-vercel-{int(time.time())}.log"
    cmd = f"vercel --prod --token={token} --yes < /dev/null > {log_path} 2>&1 &"
    subprocess.Popen(["bash", "-lc", cmd], cwd=str(REPO_ROOT))
    print(f"[prod_push] Vercel deploy kicked (bg · log {log_path})", flush=True)


def push_mvp_to_prod(slug: str, sb_dir: Path) -> dict:
    """主入口 · worker 在 state=live 前调

    Args:
      slug: MVP slug
      sb_dir: StartUP-Building/studio-demo/mvp/<slug>/ · pipeline 产物目录

    Returns:
      {copied: [paths], git_sha: str|None, vercel_kicked: bool, error: str|None}
    """
    result = {"copied": [], "git_sha": None, "vercel_kicked": False, "error": None}
    t0 = time.time()
    try:
        # 1. 拷资产（renders + bundle.zip 已经是 fe_root/assets/... · 其他需拷）
        fe_assets = REPO_ROOT / "assets" / "mvps" / slug
        result["copied"] = _copy_artifact_files(sb_dir, fe_assets, slug)
        print(f"[prod_push] {slug} · copied {len(result['copied'])} files", flush=True)

        # 2. git push · flock 防并发
        lock_path = Path("/tmp/arctura-git-push.lock")
        with open(lock_path, "w") as lockf:
            import fcntl
            try:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            except Exception:
                pass
            commit_msg = (
                f"worker · auto-publish · {slug}\n\n"
                f"Phase 9.7 Fix E · worker 生成完自动推 GitHub · 用户无需等待手动 push\n"
                f"  files: {len(result['copied'])} new/updated\n"
                f"  timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ok, sha, err = _git_push(slug, commit_msg)
            result["git_sha"] = sha
            if not ok:
                result["error"] = err
                print(f"[prod_push] {slug} · git push failed: {err}", flush=True)
                return result
            print(f"[prod_push] {slug} · pushed sha={sha[:8] if sha else '(nochange)'}", flush=True)

        # 3. Vercel deploy · 后台（git integration 断时兜底）
        _vercel_deploy_bg()
        result["vercel_kicked"] = True
    except Exception as e:
        import traceback
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        traceback.print_exc()
    finally:
        result["timing_ms"] = int((time.time() - t0) * 1000)
    return result

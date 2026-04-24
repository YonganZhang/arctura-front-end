"""blob_push · Phase 9.8 · 资产/Deployment 解耦（2026-04-25）

Context:
  Phase 9.7 Fix E 让 worker 自动 git push + vercel deploy · 但每个 MVP 触发一次
  完整 Vercel 部署 · 不 scalable · Hobby plan 每天 100 deploy 额度秒爆。

  Phase 9.8 根本解：资产走 Vercel Blob（对象存储 · 跟 code deployment 完全解耦）
  · worker 只上传 Blob + 写 KV · 0 次 Vercel redeploy · Blob URL 直接挂 CDN。

Flow:
  1. 遍历 sb_dir + fe_root/assets/mvps/<slug>/ · 收集所有资产
  2. 并发 PUT 到 Vercel Blob REST API（Python urllib · 不引 SDK）
  3. 返 {'renders': [urls], 'glb': url, 'deck_pptx': url, ...} · 给 materializer 用

Asset 清单（worker 每次产 MVP 都推这些）:
  - renders · 8 张 PNG（fe_root/assets/mvps/<slug>/renders/*.png）
  - GLB · 1 个（sb_dir/exports/<slug>.glb）
  - Exports · OBJ/MTL/FBX/IFC（sb_dir/exports/）
  - Decks · PPTX/PDF/MD（sb_dir/decks/）
  - Energy · BOQ-HK.md/csv · compliance-HK.md（sb_dir/energy/）
  - Misc · CLIENT-README.md · moodboard.png · floorplan.png
  - Bundle · bundle.zip（fe_root/assets/mvps/<slug>/bundle.zip · pipeline 产）

Env:
  BLOB_READ_WRITE_TOKEN · 从 ~/.arctura-env 读（worker systemd source）
"""
from __future__ import annotations
import os
import mimetypes
import urllib.request
import urllib.error
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

BLOB_API = "https://blob.vercel-storage.com"
API_VERSION = "7"
# Blob URL 的 CDN host · 用 SDK put 成功后返的 URL 里抓一次 · 硬编成常量（跟 store id 绑定）
#   孵化路径: https://ckayllzjbkelyvva.public.blob.vercel-storage.com/<pathname>
# 用户换 store 时改这里 + 换 BLOB_READ_WRITE_TOKEN 即可
BLOB_CDN_HOST = "https://ckayllzjbkelyvva.public.blob.vercel-storage.com"


def _guess_mime(path: Path) -> str:
    """根据扩展名返 mime · Blob 无 content-type 时按 octet-stream 传"""
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    # Vercel Blob 需要 GLB 识别
    ext = path.suffix.lower()
    if ext == ".glb":
        return "model/gltf-binary"
    if ext == ".ifc":
        return "application/x-step"
    if ext == ".fbx":
        return "application/octet-stream"
    return "application/octet-stream"


def put_blob(pathname: str, body: bytes, token: str, content_type: str = None) -> dict:
    """PUT 单文件到 Vercel Blob · 返 {url, pathname, contentType}

    Raises:
      RuntimeError · 任何 HTTP/IO 错 · 调用方 catch 决定 fail-soft 还是 raise
    """
    url = f"{BLOB_API}/{pathname.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-version": API_VERSION,
        "x-vercel-blob-access": "public",
        "x-allow-overwrite": "1",
    }
    if content_type:
        headers["x-content-type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = (e.read() or b"").decode(errors="replace")[:300]
        raise RuntimeError(f"blob PUT {pathname}: HTTP {e.code} · {body_text}")
    except Exception as e:
        raise RuntimeError(f"blob PUT {pathname}: {type(e).__name__} · {str(e)[:200]}")


def put_file(local_path: Path, blob_pathname: str, token: str) -> dict:
    """读本机文件 · PUT Blob · 返 SDK put() 同形状 dict"""
    with open(local_path, "rb") as f:
        body = f.read()
    return put_blob(blob_pathname, body, token, content_type=_guess_mime(local_path))


def _collect_assets(slug: str, sb_dir: Path, fe_root: Path) -> list[tuple[Path, str, str]]:
    """收集 MVP 所有资产 · 返 [(local_path, blob_pathname, category), ...]

    category 分类给 asset_urls 返值组结构用
    """
    assets: list[tuple[Path, str, str]] = []
    fe_slug_dir = fe_root / "assets" / "mvps" / slug

    # renders · 优先 fe_root（LIGHT pipeline 写这） · fallback sb_dir
    renders_dir = fe_slug_dir / "renders"
    if not renders_dir.is_dir():
        renders_dir = sb_dir / "renders"
    if renders_dir.is_dir():
        for p in sorted(renders_dir.iterdir()):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                assets.append((p, f"mvps/{slug}/renders/{p.name}", "render"))

    # GLB · model-viewer 硬依赖
    glb = sb_dir / "exports" / f"{slug}.glb"
    if glb.exists():
        assets.append((glb, f"mvps/{slug}/{slug}.glb", "glb"))

    # Exports · OBJ/MTL/FBX/IFC
    for ext in ("obj", "mtl", "fbx", "ifc"):
        src = sb_dir / "exports" / f"{slug}.{ext}"
        if src.exists():
            assets.append((src, f"mvps/{slug}/exports/{slug}.{ext}", f"export_{ext}"))

    # Decks
    for name in ("deck-client.pptx", "deck-client.pdf", "deck-client.md"):
        src = sb_dir / "decks" / name
        if src.exists():
            assets.append((src, f"mvps/{slug}/decks/{name}", f"deck_{name.split('.')[-1]}"))

    # Energy
    for name in ("boq-HK.md", "boq-HK.csv", "compliance-HK.md"):
        src = sb_dir / "energy" / name
        if src.exists():
            assets.append((src, f"mvps/{slug}/energy/{name}", f"energy_{name.split('.')[-1]}"))

    # Misc
    for name in ("CLIENT-README.md", "moodboard.png", "floorplan.png"):
        src = sb_dir / name
        if src.exists():
            assets.append((src, f"mvps/{slug}/{name}", "misc"))

    # Bundle · pipeline 写在 fe_root 侧
    bundle = fe_slug_dir / "bundle.zip"
    if bundle.exists():
        assets.append((bundle, f"mvps/{slug}/bundle.zip", "bundle"))

    return assets


def upload_mvp_assets(slug: str, sb_dir: Path, fe_root: Path, max_workers: int = 6) -> dict:
    """主入口 · 并发上传 MVP 所有资产到 Vercel Blob

    Returns:
      {
        "renders": [url1, url2, ...],     # 按文件名字母序
        "glb": url or None,
        "exports": {"obj": url, "fbx": url, "ifc": url, "mtl": url},
        "decks": {"pptx": url, "pdf": url, "md": url},
        "energy": {"boq_md": url, "boq_csv": url, "compliance_md": url},
        "misc": {"CLIENT-README.md": url, "moodboard.png": url, "floorplan.png": url},
        "bundle": url or None,
        "_meta": {"uploaded": N, "failed": N, "timing_ms": int, "errors": [...]}
      }
    """
    t0 = time.time()
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN 未设 · 查 ~/.arctura-env")

    assets = _collect_assets(slug, sb_dir, fe_root)
    if not assets:
        return {"renders": [], "_meta": {"uploaded": 0, "failed": 0, "timing_ms": 0, "errors": ["no assets found"]}}

    urls: dict = {
        "renders": [],
        "glb": None,
        "exports": {},
        "decks": {},
        "energy": {},
        "misc": {},
        "bundle": None,
    }
    errors: list[str] = []
    uploaded = 0

    def _upload_one(local: Path, pathname: str, category: str):
        try:
            r = put_file(local, pathname, token)
            return (category, pathname, r["url"], None)
        except Exception as e:
            return (category, pathname, None, str(e)[:200])

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_upload_one, local, pn, cat) for local, pn, cat in assets]
        for fut in as_completed(futures, timeout=120):
            cat, pn, url, err = fut.result()
            if err:
                errors.append(f"{pn}: {err}")
                continue
            uploaded += 1
            # 按 category 组结构
            if cat == "render":
                urls["renders"].append(url)
            elif cat == "glb":
                urls["glb"] = url
            elif cat.startswith("export_"):
                urls["exports"][cat.split("_", 1)[1]] = url
            elif cat.startswith("deck_"):
                urls["decks"][cat.split("_", 1)[1]] = url
            elif cat.startswith("energy_"):
                key = "boq_md" if "boq-HK.md" in pn else "boq_csv" if "boq-HK.csv" in pn else "compliance_md"
                urls["energy"][key] = url
            elif cat == "misc":
                urls["misc"][Path(pn).name] = url
            elif cat == "bundle":
                urls["bundle"] = url

    # renders 按文件名排序（确保 01_hero 在前）
    urls["renders"].sort(key=lambda u: u.split("/")[-1])

    urls["_meta"] = {
        "uploaded": uploaded,
        "failed": len(errors),
        "timing_ms": int((time.time() - t0) * 1000),
        "errors": errors[:5],  # 最多 5 条 · 避免日志爆
    }
    return urls

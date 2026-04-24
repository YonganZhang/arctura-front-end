#!/usr/bin/env bash
# Phase 9.3 · 对齐严老师 openstudio harness 到本机 EnergyPlus 25.1
# ----------------------------------------------------------
# 为什么：
#   严老师 Mac 有 EP 26.1 · 本机 OpenCloudOS 9.4 glibcxx 只到 3.4.30 · 26.1 装不上（需 3.4.32）
#   所以装 EP 25.1 Ubuntu22.04 · 但严老师 idf_builder.py 生成的 IDF 两处对 25.1 不兼容：
#     1. Version 硬编码 "26.1"  →  改 env-driven（默认仍 26.1，不破坏严老师本机）
#     2. Schedule:Compact 用 `For: Weekends Holidays`（26.1 语法）→ 25.1 段错误
#        改 `For: AllOtherDays`（25.1+ 均支持）
#
# 何时跑：
#   - 首次 pip install -e openstudio/agent-harness 之后
#   - 从 upstream git pull 后（会覆盖 patch）
set -euo pipefail

HARNESS="${HOME}/projects/公司项目/Building-CLI-Anything/CLI-Anything/openstudio/agent-harness/cli_anything/openstudio/core/idf_builder.py"

if [ ! -f "$HARNESS" ]; then
  echo "[patch] 找不到 $HARNESS · 严老师 harness 没装？"
  exit 1
fi

# 若已 patch 过 · 跳过（幂等）
if grep -q "_EP_IDF_VERSION" "$HARNESS"; then
  echo "[patch] idf_builder.py 已 patch · skip"
  exit 0
fi

# 1. Version 26.1 → env-driven
python3 - <<PY
import re
from pathlib import Path
p = Path("$HARNESS")
src = p.read_text()
src = src.replace(
    'IDF_HEADER = """!-Generator',
    'import os as _os\n_EP_IDF_VERSION = _os.environ.get("ENERGYPLUS_IDF_VERSION", "26.1")\n\nIDF_HEADER = """!-Generator',
    1,
)
src = src.replace("    26.1;                    !- Version Identifier", "    __EP_IDF_VERSION__;                    !- Version Identifier")
src = src.replace(
    "parts.append(IDF_HEADER.format(",
    "parts.append(IDF_HEADER.replace(\"__EP_IDF_VERSION__\", _EP_IDF_VERSION).format(",
)
# 2. Weekends Holidays → AllOtherDays
src = src.replace("For: Weekends Holidays,", "For: AllOtherDays,")
p.write_text(src)
print("[patch] ✅ idf_builder.py 已 patch · EP IDF version = env ENERGYPLUS_IDF_VERSION (default 26.1)")
print("[patch] ✅ Schedule:Compact 'Weekends Holidays' → 'AllOtherDays'")
PY

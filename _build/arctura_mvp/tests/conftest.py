"""pytest 共享 fixtures · 注入 KV mock · 加载真实 MVP brief 样本"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest

# 让 `from _build.arctura_mvp...` 可用
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir():
    return FIXTURES


@pytest.fixture
def brief_book_cafe():
    return json.loads((FIXTURES / "brief-22-boutique-book-cafe.json").read_text())


@pytest.fixture
def brief_principal_office():
    return json.loads((FIXTURES / "brief-50-principal-office.json").read_text())


@pytest.fixture
def mvp_study_room():
    return json.loads((FIXTURES / "mvp-01-study-room.json").read_text())


# ───── In-memory KV mock（代替 Upstash REST）─────

class KVMock:
    """Redis-like in-memory mock · 覆盖 _core.py 用到的命令"""
    def __init__(self):
        self.store = {}
        self.zsets = {}
        self.ttls = {}

    def get(self, key): return self.store.get(key)

    def set(self, key, value, *, ex=None):
        self.store[key] = str(value)
        if ex is not None: self.ttls[key] = ex
        return True

    def set_json(self, key, obj, *, ex=None):
        return self.set(key, json.dumps(obj), ex=ex)

    def get_json(self, key):
        v = self.get(key)
        return json.loads(v) if v else None

    def delete(self, *keys):
        n = 0
        for k in keys:
            if k in self.store: del self.store[k]; n += 1
            if k in self.zsets: del self.zsets[k]; n += 1
            if k in self.ttls: del self.ttls[k]
        return n

    def persist(self, key):
        if key in self.ttls: del self.ttls[key]
        return True

    def exists(self, *keys):
        return sum(1 for k in keys if k in self.store or k in self.zsets)

    def expire(self, key, seconds):
        self.ttls[key] = seconds
        return True

    def zadd(self, key, score, member):
        zs = self.zsets.setdefault(key, {})
        new = member not in zs
        zs[member] = score
        return 1 if new else 0

    def zrevrange(self, key, start=0, stop=-1, *, with_scores=False):
        zs = self.zsets.get(key, {})
        sorted_items = sorted(zs.items(), key=lambda x: -x[1])
        if stop == -1:
            slice_end = len(sorted_items)
        else:
            slice_end = stop + 1
        return [m for m, _ in sorted_items[start:slice_end]]

    def zcard(self, key):
        return len(self.zsets.get(key, {}))

    def zrem(self, key, member):
        zs = self.zsets.get(key)
        if zs and member in zs: del zs[member]; return 1
        return 0

    def ping(self): return True


@pytest.fixture
def kv_mock(monkeypatch):
    m = KVMock()
    from _build.arctura_mvp.store import kv as kv_mod
    for fn in ["get", "set", "set_json", "get_json", "delete", "persist",
               "exists", "expire", "zadd", "zrevrange", "zcard", "zrem", "ping"]:
        if hasattr(kv_mod, fn):
            monkeypatch.setattr(kv_mod, fn, getattr(m, fn))
    return m

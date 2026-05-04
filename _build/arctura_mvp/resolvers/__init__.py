"""Phase 11.7 · Resolver 注册表 · 一劳永逸防"输入塌缩 default" 反模式

ADR-003 落地核心。背景：之前两个 bug（scene-default-fallback / palette-fallback）都是
同 shape：dict.get(x, default) · LLM/用户输入不在 key 列表 → 全 fallback 到 default →
"无论用户写啥都同输出"。单测验"default 自身正确"反而强化了 fallback 看起来正常的假象。

这个模块提供：
1. Resolver 抽象：每个 enum-based lookup 必须注册（name + enum + keywords + dirty_fixtures + fallback_name）
2. 通用 resolve 算法：关键词包含匹配 + 词边界 + 多命中并集
3. REGISTRY 中央表：单测自动遍历做 differential testing
4. Differential 不变式：
   (a) 每 enum 值 resolve 到自己
   (b) 每 dirty fixture 不塌到 fallback（除非显式标 expect_fallback=True）
   (c) 不同 enum 输入 → 不同输出（防同质化）

新增 resolver 流程：
    from _build.arctura_mvp.resolvers import Resolver, register
    R = Resolver(
        name="region",
        enum=["HK", "CN", "INTL"],
        keywords={"HK": ["hk", "hong kong", "香港"], ...},
        dirty_fixtures=[("Singapore", None), ("中国", "CN")],  # None = 期望非 fallback 即可
        fallback="HK",
    )
    register(R)
→ test_no_collapse_invariants_via_registry 自动覆盖所有锁定。
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


_ASCII_RE = re.compile(r"^[\x00-\x7F]+$")


@dataclass
class Resolver:
    """通用 enum-based input resolver

    Args:
        name: resolver 唯一标识（用于注册表 key + 测试报错信息）
        enum: 合法标准值列表（譬如 ["HK","CN","INTL"]）
        keywords: 标准值 → 关键词列表 dict · 关键词包含匹配 · 中文 substring · 英文词边界
        dirty_fixtures: list[(real_input, expected_std_or_None)]
            - real_input: LLM/用户可能写出的脏字符串
            - expected_std_or_None: 若 None · 仅断言"不塌到 fallback" · 若 std 值 · 断言精确命中
        fallback: 全 miss 时返的 std 值（必须 ∈ enum 或为 "default" 表示元 fallback）
        case_insensitive: 关键词匹配是否忽略大小写（默认 True）
        normalize_underscore: 输入 _ → 空格预处理（譬如 "living_room" → "living room"）
    """
    name: str
    enum: list[str]
    keywords: dict[str, list[str]]
    fallback: str
    dirty_fixtures: list[tuple[str, Optional[str]]] = field(default_factory=list)
    case_insensitive: bool = True
    normalize_underscore: bool = True

    def __post_init__(self):
        if self.fallback not in self.enum and self.fallback != "default":
            raise ValueError(
                f"resolver '{self.name}' fallback={self.fallback!r} 不在 enum={self.enum} "
                f"也不是元 'default' · 必须明确指定")
        # 检查 keywords keys 是 enum 子集
        unknown = set(self.keywords.keys()) - set(self.enum)
        if unknown:
            raise ValueError(
                f"resolver '{self.name}' keywords 含 enum 没有的 key: {unknown}")

    def resolve(self, raw: Optional[str]) -> list[str]:
        """返命中的 std 值列表（保序去重）· 全 miss → [fallback]"""
        if raw is None:
            return [self.fallback]
        text = str(raw).strip()
        if self.case_insensitive:
            text = text.lower()
        if not text:
            return [self.fallback]
        if self.normalize_underscore:
            text = text.replace("_", " ")

        hits: list[tuple[int, str]] = []
        for std, kws in self.keywords.items():
            for kw in kws:
                kw_lower = kw.lower() if self.case_insensitive else kw
                idx = -1
                if _ASCII_RE.match(kw_lower):
                    m = re.search(rf"\b{re.escape(kw_lower)}\b", text)
                    if m:
                        idx = m.start()
                else:
                    p = text.find(kw_lower)
                    if p >= 0:
                        idx = p
                if idx >= 0:
                    hits.append((idx, std))
                    break

        if not hits:
            return [self.fallback]

        hits.sort(key=lambda x: x[0])
        seen, out = set(), []
        for _, std in hits:
            if std not in seen:
                seen.add(std)
                out.append(std)
        return out

    def resolve_first(self, raw: Optional[str]) -> str:
        """单值版本 · 多命中取第一个"""
        return self.resolve(raw)[0]


# ───── 中央注册表 ─────

_REGISTRY: dict[str, Resolver] = {}


def register(resolver: Resolver) -> Resolver:
    """注册 resolver · 重复注册会抛（防 silent override）"""
    if resolver.name in _REGISTRY:
        raise ValueError(f"resolver '{resolver.name}' 已注册 · 不允许重复（防 silent override）")
    _REGISTRY[resolver.name] = resolver
    return resolver


def get(name: str) -> Resolver:
    if name not in _REGISTRY:
        raise KeyError(f"resolver '{name}' 未注册 · 已注册：{sorted(_REGISTRY.keys())}")
    return _REGISTRY[name]


def all_resolvers() -> list[Resolver]:
    return list(_REGISTRY.values())


__all__ = ["Resolver", "register", "get", "all_resolvers"]


# ───── 注册所有现有 resolver（一处真源 · 元测试自动覆盖）─────

# space.type · 已在 generators/_resolve_space_type.py 用裸函数实现 · 这里包成 Resolver 入注册表
import json as _json
from pathlib import Path as _Path

_FIXTURE_PATH = _Path(__file__).resolve().parents[3] / "api" / "_shared" / "space-type-keywords.json"
_SPACE_KW = _json.loads(_FIXTURE_PATH.read_text())["keywords"]
_SPACE_ENUM = _json.loads(_FIXTURE_PATH.read_text())["enum"]


SPACE_TYPE = register(Resolver(
    name="space_type",
    enum=_SPACE_ENUM,
    keywords=_SPACE_KW,
    fallback="multipurpose",  # 全 miss 当 multipurpose · 而非"default"（用户 face）
    dirty_fixtures=[
        # LLM 可能写的脏字符串 · 都不该塌到 fallback
        ("hybrid cafe-office", "cafe"),       # 多命中 · 第一个是 cafe
        ("校长办公室", "office"),
        ("principal office", "office"),
        ("showroom cafe", "gallery"),         # showroom 命中 gallery
        ("dental clinic", "clinic"),
        ("co-working space", "multipurpose"),
        ("boutique retail store", "retail"),
        ("contemporary office", "office"),
        ("modern living", "living_room"),
    ],
))


# region · 用户可能写"Singapore"/"中国"/"USA" · 之前 fallback HK 3500
REGION = register(Resolver(
    name="region",
    enum=["HK", "CN", "INTL"],
    keywords={
        "HK":   ["hk", "hong kong", "香港", "hongkong"],
        "CN":   ["cn", "china", "中国", "中国大陆", "mainland", "内地"],
        "INTL": ["intl", "international", "海外", "国际", "global",
                 "us", "usa", "美国", "uk", "england", "英国", "europe", "欧洲",
                 "japan", "日本", "jp", "singapore", "新加坡", "sg",
                 "australia", "澳洲", "au", "canada", "加拿大", "ca"],
    },
    fallback="INTL",   # 不认识的国家放 INTL 而非 HK · 至少不会数据错（INTL 价格更高 · 用户会问起）
    dirty_fixtures=[
        ("Singapore", "INTL"),
        ("US", "INTL"),
        ("中国大陆", "CN"),
        ("Hong Kong", "HK"),
        ("hong kong", "HK"),
        ("HK", "HK"),
        ("Japan", "INTL"),
        ("英国", "INTL"),
    ],
))


# building category · materializer.py 之前 light_by_cat fallback 8
# 现在改为 enum lookup · 不认识的 category 走 multipurpose 8 W/m²（保守值）
BUILDING_CATEGORY = register(Resolver(
    name="building_category",
    enum=["hospitality", "workplace", "residential", "civic", "wellness", "retail", "education", "multipurpose"],
    keywords={
        "hospitality": ["hospitality", "hotel", "酒店", "旅店", "民宿", "bnb", "restaurant", "餐厅", "酒吧", "bar", "cafe", "咖啡"],
        "workplace":   ["workplace", "office", "办公", "co-working", "coworking", "studio", "工作室", "boardroom"],
        "residential": ["residential", "home", "house", "住宅", "公寓", "apartment", "卧室", "bedroom", "客厅", "living"],
        "civic":       ["civic", "公共", "library", "图书馆", "community", "社区", "office of the principal", "校长"],
        "wellness":    ["wellness", "spa", "fitness", "yoga", "瑜伽", "健身", "clinic", "诊所", "dental", "医疗", "healthcare"],
        "retail":      ["retail", "shop", "store", "店铺", "零售", "boutique", "showroom", "gallery", "画廊"],
        "education":   ["education", "教育", "classroom", "教室", "school", "学校", "training", "培训"],
        "multipurpose":["multipurpose", "mixed-use", "hybrid", "多功能", "复合"],
    },
    fallback="multipurpose",   # 不认识 → multipurpose（中性值）· 不再永远塌到 workplace=9
    dirty_fixtures=[
        ("dental clinic", "wellness"),
        ("校长办公室", "civic"),       # 校长 → civic（学校）
        ("co-working space", "workplace"),
        ("boutique cafe", "hospitality"),  # cafe 优先（hospitality 列表第一）· 现实合理
        ("yoga studio", "wellness"),
        ("kids classroom", "education"),
        ("luxury showroom", "retail"),
    ],
))


# 灯光密度 W/m² 按 category 取值（之前 hardcoded dict）· 这里只暴露 cat→density 函数
# resolver 本身只负责 cat resolve · density 是单独 mapping
LIGHTING_DENSITY_W_M2_BY_CAT: dict[str, float] = {
    "hospitality":  11.0,
    "workplace":    9.0,
    "residential":  6.0,
    "civic":        8.0,
    "wellness":     10.0,
    "retail":       12.0,
    "education":    8.5,
    "multipurpose": 8.0,   # 中性值
}


# 每方造价 HK$/m² · 按 region · 替代 derive/__init__.py:110 hardcoded
COST_PER_M2_BY_REGION: dict[str, int] = {
    "HK":   3500,
    "CN":   2200,
    "INTL": 4800,   # INTL 走偏高（新加坡/美国更贵）
}

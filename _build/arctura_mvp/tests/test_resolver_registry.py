"""Phase 11.7 · Resolver 注册表元测试 · 一劳永逸防 fallback 塌缩

ADR-003 落地：所有 enum-based lookup 必须注册到 _build/arctura_mvp/resolvers/
本测试自动遍历注册表，对每个 resolver 跑同一套不变式：

  (a) **enum 自洽** · 每 enum 值 resolve 到自己（不塌到别的 std）
  (b) **dirty 不塌 fallback** · dirty_fixtures 输入不该全 fallback（除非显式标）
  (c) **enum 互不塌** · enum 两两输入产出必须不同（防表项重复）

加新 resolver：
  在 resolvers/__init__.py 调 register(Resolver(...)) → 测试自动覆盖。
不需要改这个测试文件。
"""
import pytest
from _build.arctura_mvp.resolvers import all_resolvers, get


@pytest.mark.parametrize("resolver", all_resolvers(), ids=lambda r: r.name)
def test_resolver_enum_self_consistent(resolver):
    """每个 enum 值作为输入必须 resolve 到包含自己（防 enum 之间互相吞）"""
    for std in resolver.enum:
        out = resolver.resolve(std)
        assert std in out, f"{resolver.name}: enum '{std}' 不能 resolve 到自己 · 实际 {out}"


@pytest.mark.parametrize("resolver", all_resolvers(), ids=lambda r: r.name)
def test_resolver_dirty_input_does_not_collapse_to_fallback(resolver):
    """dirty_fixtures 都是真实"用户/LLM 会写的脏字符串"·必须不塌到 fallback"""
    if not resolver.dirty_fixtures:
        pytest.skip(f"{resolver.name} 没声明 dirty_fixtures · 加几个真实脏输入入注册表")

    failures = []
    for raw, expected in resolver.dirty_fixtures:
        out = resolver.resolve(raw)
        first = out[0]
        if expected is None:
            # 仅断言不塌 fallback
            if first == resolver.fallback:
                failures.append(f"  '{raw}' → {out} · 塌到 fallback={resolver.fallback}")
        else:
            # 精确断言
            if expected not in out:
                failures.append(f"  '{raw}' → {out} · 期望含 '{expected}'")

    assert not failures, f"\n{resolver.name} dirty_fixtures 失败：\n" + "\n".join(failures)


@pytest.mark.parametrize("resolver", all_resolvers(), ids=lambda r: r.name)
def test_resolver_keywords_no_double_mapping(resolver):
    """同一关键词不能映射到两个 enum（譬如 'cafe' 不能既是 hospitality 又是 retail）"""
    seen_kw_to_std = {}
    for std, kws in resolver.keywords.items():
        for kw in kws:
            kl = kw.lower() if resolver.case_insensitive else kw
            if kl in seen_kw_to_std and seen_kw_to_std[kl] != std:
                pytest.fail(
                    f"{resolver.name}: 关键词 '{kw}' 同时映射到 "
                    f"'{seen_kw_to_std[kl]}' 跟 '{std}' · 解析结果不确定")
            seen_kw_to_std[kl] = std


@pytest.mark.parametrize("resolver", all_resolvers(), ids=lambda r: r.name)
def test_resolver_enum_inputs_produce_distinct_outputs(resolver):
    """N 个 enum 输入 → 至少 N 种不同 resolve 结果（防 enum 互相吞）"""
    if len(resolver.enum) < 2:
        pytest.skip("enum 太少不需要差分")
    outputs = {std: tuple(resolver.resolve(std)) for std in resolver.enum}
    distinct_count = len(set(outputs.values()))
    assert distinct_count >= len(resolver.enum), (
        f"{resolver.name}: {len(resolver.enum)} enum 只产 {distinct_count} 种结果 · "
        f"说明有 enum 互吞（关键词冲突）· 详 {outputs}")


@pytest.mark.parametrize("resolver", all_resolvers(), ids=lambda r: r.name)
def test_resolver_full_miss_returns_fallback(resolver):
    """完全无关字符串必须返 [fallback] · 单值 · 不是空列表 / 异常"""
    out = resolver.resolve("xyzqq alien gibberish 999")
    assert out == [resolver.fallback], f"{resolver.name}: 全 miss 应返 [{resolver.fallback}] · 实际 {out}"

    out_none = resolver.resolve(None)
    assert out_none == [resolver.fallback]

    out_empty = resolver.resolve("")
    assert out_empty == [resolver.fallback]


# ───── 注册表自身完整性 ─────

def test_registry_has_known_resolvers():
    """注册表必须包含核心 resolver · 删一个就报警"""
    REQUIRED = ["space_type", "region", "building_category"]
    from _build.arctura_mvp.resolvers import _REGISTRY
    for name in REQUIRED:
        assert name in _REGISTRY, f"必有 resolver '{name}' 缺 · 谁删了？"


def test_registry_no_duplicate_register():
    """重复注册同名 resolver 必须抛（防 silent override）"""
    from _build.arctura_mvp.resolvers import register, Resolver
    R = Resolver(
        name="space_type",   # 已注册
        enum=["a"], keywords={"a": ["a"]}, fallback="a",
    )
    with pytest.raises(ValueError, match="已注册"):
        register(R)


def test_registry_fallback_must_be_in_enum():
    """fallback 必须 ∈ enum 否则 resolve 返不合法值"""
    from _build.arctura_mvp.resolvers import Resolver
    with pytest.raises(ValueError, match="不在 enum"):
        Resolver(
            name="bad", enum=["a", "b"], keywords={"a": ["a"]},
            fallback="not_in_enum",
        )


def test_registry_keywords_keys_subset_of_enum():
    """keywords 的 key 必须 ⊆ enum"""
    from _build.arctura_mvp.resolvers import Resolver
    with pytest.raises(ValueError, match="enum 没有的 key"):
        Resolver(
            name="bad2", enum=["a", "b"], keywords={"x": ["x"]},
            fallback="a",
        )


# ───── 跟现有 resolver 跨语言一致（space_type · _resolve_space_type.py 是裸函数版本）─────

def test_space_type_resolver_equivalent_to_legacy_function():
    """注册表里的 space_type Resolver 应跟 generators/_resolve_space_type.py 同行为
    （防新接口跟老路径漂移）"""
    from _build.arctura_mvp.generators._resolve_space_type import resolve_space_type
    from _build.arctura_mvp.resolvers import get
    R = get("space_type")

    test_inputs = ["office", "cafe", "hybrid cafe-office", "校长办公室", "alien xyz"]
    for raw in test_inputs:
        legacy_out = resolve_space_type(raw)
        new_out = R.resolve(raw)
        # legacy 全 miss 返 ["default"] · 新 Resolver 全 miss 返 [fallback="multipurpose"]
        # 其他情况：命中集合应该完全一致（"default" 在 legacy 不会跟其他真命中混在一起）
        if legacy_out == ["default"]:
            assert new_out == ["multipurpose"], \
                f"'{raw}' legacy=default 但新 resolver={new_out} · 应是 multipurpose"
        else:
            # 真命中集合必须一致（包括 multipurpose 当作 hybrid 关键词的真命中场景）
            assert set(legacy_out) == set(new_out), \
                f"'{raw}' legacy={legacy_out} new={new_out} 命中漂移"

"""Phase 11.4 后审 · 跨语言一致性 · 真测 Python apply_overrides_to_scene 行为锁

子智能体审查 #4 + Gemini ADR 审查 #6 都 flag 了这个测试缺：
原本 JS 跟 Python 各自单元测试绿，但**没有用同一份 fixture 跑两边对比结果**。

策略：
  1. 加载共享 fixture cross_lang_apply_overrides.json（顶层 cases 数组）
  2. Python 端跑 apply_overrides_to_scene · 校验每个 case 的 expected_invariants
  3. JS 端在 _tests/unit/cross-lang-overrides-apply.test.mjs 用同 fixture 跑同样校验
  4. 若 Python/JS 行为不对称 · 至少一边的"不变式断言"会挂 · 早暴露 drift
"""
import json
from pathlib import Path
import pytest

from _build.arctura_mvp.derive.overrides import apply_overrides_to_scene

FIXTURE = Path(__file__).parent / "fixtures" / "cross_lang_apply_overrides.json"


def _load_cases():
    return json.loads(FIXTURE.read_text())["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["name"])
def test_python_applies_fixture_invariants(case):
    """每个 case 跑 Python apply · 验 expected_invariants · JS 端会跑同 fixture · 双绿 = 行为对称"""
    base = case["base_scene"]
    overrides = case["overrides"]
    inv = case["expected_invariants"]

    final = apply_overrides_to_scene(base, overrides)

    # 通用断言（每 case 选用部分）
    if "objects_count" in inv:
        assert len(final.get("objects", [])) == inv["objects_count"], \
            f"{case['name']}: objects 数 {len(final.get('objects', []))} ≠ 期望 {inv['objects_count']}"

    if "objects_contains_id" in inv:
        ids = [o.get("id") for o in final.get("objects", [])]
        assert inv["objects_contains_id"] in ids, \
            f"{case['name']}: objects 缺 {inv['objects_contains_id']} · ids={ids}"

    if "floor_material" in inv:
        assert final.get("floor", {}).get("material_id") == inv["floor_material"], \
            f"{case['name']}: floor.material_id 不对"

    if "asm_desk_1_pos" in inv:
        asm = next((a for a in final.get("assemblies", []) if a.get("id") == "asm_desk_1"), None)
        assert asm and asm.get("pos") == inv["asm_desk_1_pos"], \
            f"{case['name']}: asm_desk_1.pos 不对 · 实际 {asm and asm.get('pos')}"

    if "asm_real_pos" in inv:
        asm = next((a for a in final.get("assemblies", []) if a.get("id") == "asm_real"), None)
        assert asm and asm.get("pos") == inv["asm_real_pos"], \
            f"{case['name']}: orphan 该被静默跳过 · 但 asm_real.pos 被改了"

    if "lights_count" in inv:
        assert len(final.get("lights", [])) == inv["lights_count"], \
            f"{case['name']}: lights 数 {len(final.get('lights', []))} ≠ 期望"

    if "sun_1_intensity" in inv:
        sun = next((l for l in final.get("lights", []) if l.get("id") == "sun_1"), None)
        assert sun and abs(sun.get("intensity", 0) - inv["sun_1_intensity"]) < 0.001, \
            f"{case['name']}: sun_1.intensity 不对 · 实际 {sun and sun.get('intensity')}"


def test_apply_order_enforced_internally():
    """ADR-001 §"应用顺序" Gemini 反馈：用户给的 overrides dict 顺序不重要 ·
    内部按 tombstones→appearance→layout→structural→lighting 强制顺序应用。

    锁定方式：构造一个 dict 倒序键插入 · 应用结果跟正序一样。
    （Python dict 3.7+ 保插入顺序 · 我们的实现按硬编码顺序遍历 namespace · 不依赖 dict 顺序）
    """
    base = {
        "bounds": {"w": 5, "d": 4, "h": 2.8}, "walls": [],
        "objects": [{"id": "obj_x", "pos": [0, 0, 0]}],
        "assemblies": [], "lights": [], "materials": {}, "floor": {}, "ceiling": {},
    }

    # 倒序输入：先 lighting 再 layout 再 tombstones
    overrides_reversed = {
        "lighting": {"_added": [{"id": "new_l", "type": "point"}]},
        "layout": {"o1": {"target": "object", "target_id": "obj_x", "pos": [1, 1, 0]}},
        "tombstones": {"objects": []},   # 空 · 不删任何
    }
    overrides_normal = {
        "tombstones": {"objects": []},
        "layout": {"o1": {"target": "object", "target_id": "obj_x", "pos": [1, 1, 0]}},
        "lighting": {"_added": [{"id": "new_l", "type": "point"}]},
    }

    s1 = apply_overrides_to_scene(base, overrides_reversed)
    s2 = apply_overrides_to_scene(base, overrides_normal)

    # 关键不变量都该相同
    assert s1["objects"][0]["pos"] == s2["objects"][0]["pos"] == [1, 1, 0]
    assert len(s1["lights"]) == len(s2["lights"]) == 1
    assert s1["lights"][0]["id"] == s2["lights"][0]["id"] == "new_l"

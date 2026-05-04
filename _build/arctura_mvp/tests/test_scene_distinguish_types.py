"""Phase 11.1 · 锁住 today's bug 不复现：

scene generator 对不同 space.type 必须生成有别的家具组合。
今天的 bug：office / cafe / clinic / 校长办公室 全部走 default → 永远同一个 scene。
"""
from _build.arctura_mvp.generators import build_scene_from_brief


def _brief(space_type, area=30):
    return {
        "project": {"name_cn": "T", "name_en": "T"},
        "space": {"area_sqm": area, "type": space_type},
        "style": {"keywords": ["极简"]},
        "functional_zones": [{"name": "工作区"}],
    }


def _furniture_types(scene):
    """从 scene.assemblies 抽家具类型集合（去除装饰 clutter · 只看主家具）"""
    DECOR = {"book", "vase", "cup", "plant_small", "picture_frame"}
    return {a["type"] for a in scene["assemblies"] if a["type"] not in DECOR}


def test_office_and_cafe_furniture_differ():
    """office vs cafe 家具集合必须 ≠ · 这是今天 bug 的精确 reproduce 锁"""
    s_office = build_scene_from_brief(_brief("office"), "t1")
    s_cafe = build_scene_from_brief(_brief("cafe"), "t2")
    assert _furniture_types(s_office) != _furniture_types(s_cafe), \
        "office 跟 cafe 必须有家具差别 · 否则今天 bug 复现"
    # office 一定有 desk
    assert "desk_standard" in _furniture_types(s_office)
    # cafe 一定有 dining table
    assert "table_dining" in _furniture_types(s_cafe)


def test_hybrid_cafe_office_uses_both():
    """混合场景 LLM 写 type='hybrid cafe-office' · 必须**同时**有 cafe + office 代表家具
    （Codex Step 1 #1：原 OR assert 太松，cafe-only 或 office-only 都会过）"""
    s = build_scene_from_brief(_brief("hybrid cafe-office"), "t")
    types = _furniture_types(s)
    assert "table_dining" in types, f"hybrid 缺 cafe 代表 table_dining · types={types}"
    assert "desk_standard" in types, f"hybrid 缺 office 代表 desk_standard · types={types}"
    # 不应该是 default 的 3 件家具
    assert types != {"chair_standard", "table_coffee", "lamp_floor"}, \
        "hybrid 居然 fallback 到 default · 关键词解析失效"


def test_principal_office_routes_to_office():
    """LLM 写 'principal office' / '校长办公室' · 必须命中 office 默认家具"""
    s1 = build_scene_from_brief(_brief("principal office"), "t1")
    s2 = build_scene_from_brief(_brief("校长办公室"), "t2")
    assert "desk_standard" in _furniture_types(s1)
    assert "desk_standard" in _furniture_types(s2)


def test_clinic_distinct_from_office():
    """clinic / 牙科诊所 · 跟 office 默认家具集合可有重叠但不能完全相同"""
    s_office = build_scene_from_brief(_brief("office"), "t1")
    s_clinic = build_scene_from_brief(_brief("dental clinic"), "t2")
    types_o = _furniture_types(s_office)
    types_c = _furniture_types(s_clinic)
    assert types_o != types_c
    # clinic 默认含 chair_lounge（候诊区 · office 没有）
    assert "chair_lounge" in types_c


def test_unknown_type_falls_back_to_default():
    """完全不认识的 type · 应回 default 三件家具（不是抛错）"""
    s = build_scene_from_brief(_brief("totally unknown alien type xyz"), "t")
    types = _furniture_types(s)
    # default 是 chair_standard + table_coffee + lamp_floor
    assert "chair_standard" in types
    assert "table_coffee" in types
    assert "lamp_floor" in types


def test_extreme_hybrid_string_is_capped():
    """对抗性 type 字符串覆盖所有 10 enum · 必须 cap 到 8 件主家具内（不溢出布局）"""
    extreme = "office cafe clinic showroom retail dining bedroom living room library co-working"
    s = build_scene_from_brief(_brief(extreme), "t")
    main = _furniture_types(s)
    assert len(main) <= 8, f"主家具数 {len(main)} 超 cap=8 · 房间会塞不下"


def test_study_room_routes_to_study_not_office():
    """'study room' 必须命中 study · 不该被 office 抢（Codex Step 1 #2）"""
    from _build.arctura_mvp.generators._resolve_space_type import resolve_space_type
    out = resolve_space_type("study room")
    assert "study" in out
    # office 跟 study 默认家具一样 · 但意图不同 · 至少 resolve 阶段必须分开
    assert out[0] == "study", f"study room 应优先映射 study · 实际 {out}"


def test_each_enum_distinct_from_default():
    """每个 enum 默认家具集合都不应该等同于 default(3件) · 否则等于没用"""
    DEFAULT_TYPES = {"chair_standard", "table_coffee", "lamp_floor"}
    from _build.arctura_mvp.generators._resolve_space_type import list_enum
    for std_type in list_enum():
        s = build_scene_from_brief(_brief(std_type), "t")
        types = _furniture_types(s)
        assert types != DEFAULT_TYPES, \
            f"{std_type} 生成的家具组 {types} 跟 default 一样 · _DEFAULTS_BY_TYPE 没真区分"

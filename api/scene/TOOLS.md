# LLM Tool Schema · Phase 2.0 Scene Editing

> **在 Phase 1.8 已有的 5 个项目级 tool 之上扩展**。用户通过 chat 改 scene 的入口。所有 tool 最终都映射到 `/api/scene/ops` 的 ops。

## Tool → Op 映射表

| Tool name | 目标 Op | 作用 |
|---|---|---|
| `move_furniture` | `move_object` / `rotate_object` | 移动 / 旋转家具 |
| `resize_furniture` | `resize_object` | 改家具尺寸 |
| `remove_furniture` | `remove_object` | 删家具 |
| `add_furniture` | `add_object` | 加家具（从家具库） |
| `change_material` | `change_material` | 改物体 / 墙 / 地板 / 天花材质 |
| `add_light` | `add_light` | 加光源 |
| `change_light` | `change_light` | 改 CCT / 功率 |
| `remove_light` | `remove_light` | 删光源 |
| `move_wall` | `move_wall` | 移墙（顶点） |
| `resize_wall` | `resize_wall` | 改墙高 / 厚 |
| `add_window` | `add_opening (type:window)` | 加窗 |
| `add_door` | `add_opening (type:door)` | 加门 |
| `remove_opening` | `remove_opening` | 删窗/门 |

Phase 1.8 原有标量 tool（保留，不变）：`set_editable`, `scale_editable`, `switch_variant`, `switch_region`, `append_timeline`。

## Tool 定义（OpenAI function calling 格式）

### move_furniture

```json
{
  "name": "move_furniture",
  "description": "移动或旋转某个家具。用户说'把衣柜往左移 30cm' / '把沙发转 90 度'时用",
  "parameters": {
    "type": "object",
    "required": ["id_or_name"],
    "properties": {
      "id_or_name": {
        "type": "string",
        "description": "家具 id（如 obj_closet_1）或中英文名（如 '衣柜' / 'closet'）· 后端做模糊匹配"
      },
      "pos_absolute": {
        "type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
        "description": "新坐标 [x, y, z]（米）· 与 delta 二选一"
      },
      "pos_delta": {
        "type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
        "description": "相对移动 [dx, dy, dz]（米）· 如 [-0.3, 0, 0] = 向 x 负方向移 30cm"
      },
      "rotation_deg": {
        "type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
        "description": "欧拉度数 [rx, ry, rz]· 可单独给"
      }
    }
  }
}
```

### resize_furniture

```json
{
  "name": "resize_furniture",
  "description": "改家具尺寸。用户说'把桌子加长 20cm' / '把床改成 180×200'时用",
  "parameters": {
    "type": "object",
    "required": ["id_or_name"],
    "properties": {
      "id_or_name": {"type": "string"},
      "size": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
               "description": "绝对尺寸 [w, d, h]（米）· 与 scale 二选一"},
      "scale": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
                "description": "缩放倍数 · 如 [1.2, 1, 1] = x 方向放大 20%"}
    }
  }
}
```

### remove_furniture

```json
{
  "name": "remove_furniture",
  "description": "删除家具。用户说'删衣柜' / '把笔记本拿走'时用",
  "parameters": {
    "type": "object",
    "required": ["id_or_name"],
    "properties": {
      "id_or_name": {"type": "string"}
    }
  }
}
```

### add_furniture

```json
{
  "name": "add_furniture",
  "description": "添加家具。用户说'加一把椅子' / '在窗边放个沙发'时用。type 必须是家具库里的 key",
  "parameters": {
    "type": "object",
    "required": ["type", "pos"],
    "properties": {
      "type": {
        "type": "string",
        "description": "家具库 key · 必须是可用类型之一（列表由服务端注入 prompt）· 未知 type 会被拒绝"
      },
      "pos": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
              "description": "位置 [x, y, z]（米）· z 一般 = default_size[2]/2（物体底贴地）"},
      "rotation_deg": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
      "zone": {"type": "string", "description": "所属 functional zone · 可选"},
      "label_zh": {"type": "string", "description": "中文标签 · 可选"}
    }
  }
}
```

### change_material

```json
{
  "name": "change_material",
  "description": "改材质 / 颜色。用户说'把墙刷米色' / '沙发换成胡桃木' / '地板深色'时用",
  "parameters": {
    "type": "object",
    "required": ["target"],
    "properties": {
      "target": {
        "type": "string",
        "description": "目标：家具 id / 家具名 / 墙 id（wall_N 等） / 'floor' / 'ceiling'"
      },
      "material_id": {
        "type": "string",
        "description": "已有 material_id（见 scene.materials） · 与 base_color 二选一"
      },
      "base_color": {
        "type": "string",
        "pattern": "^#[0-9a-fA-F]{6}$",
        "description": "直接给颜色 hex · 后端自动生成 inline material"
      }
    }
  }
}
```

### add_light

```json
{
  "name": "add_light",
  "description": "加光源。用户说'加个落地灯' / '顶上来个吊灯'时用",
  "parameters": {
    "type": "object",
    "required": ["type", "pos"],
    "properties": {
      "type": {"enum": ["pendant", "point", "area", "spot"]},
      "pos": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
      "cct": {"type": "integer", "minimum": 1500, "maximum": 6500, "default": 3000},
      "power": {"type": "number", "minimum": 0, "maximum": 500, "default": 60}
    }
  }
}
```

### change_light

```json
{
  "name": "change_light",
  "description": "改光源属性。用户说'把灯调暖一点' / '吊灯功率调到 80W'时用",
  "parameters": {
    "type": "object",
    "required": ["id_or_name"],
    "properties": {
      "id_or_name": {"type": "string", "description": "光源 id / 'all' / zone 名"},
      "cct": {"type": "integer"},
      "power": {"type": "number"},
      "intensity_scale": {"type": "number", "description": "倍率 · 如 1.5 = 亮度 150%"}
    }
  }
}
```

### remove_light

```json
{
  "name": "remove_light",
  "description": "删光源",
  "parameters": {
    "type": "object", "required": ["id_or_name"],
    "properties": {"id_or_name": {"type": "string"}}
  }
}
```

### move_wall

```json
{
  "name": "move_wall",
  "description": "移墙。用户说'把北墙往里挪 50cm' / '改房间形状'时用。谨慎 · 会影响面积",
  "parameters": {
    "type": "object",
    "required": ["id"],
    "properties": {
      "id": {"type": "string"},
      "start": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
      "end":   {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
      "offset": {
        "type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
        "description": "相对整体平移 [dx, dy, dz] · 与 start/end 二选一"
      }
    }
  }
}
```

### resize_wall

```json
{
  "name": "resize_wall",
  "description": "改墙高 / 墙厚。用户说'层高加到 3.2 米' / '墙加厚'时用",
  "parameters": {
    "type": "object", "required": ["id"],
    "properties": {
      "id": {"type": "string"},
      "height": {"type": "number"},
      "thickness": {"type": "number"}
    }
  }
}
```

### add_window / add_door

```json
{
  "name": "add_window",
  "description": "在墙上开窗。用户说'北墙加个窗' / '窗户挪到中间'时用（后者先 remove 再 add）",
  "parameters": {
    "type": "object",
    "required": ["wall_id", "pos_along", "width", "height"],
    "properties": {
      "wall_id": {"type": "string"},
      "pos_along": {"type": "number", "description": "沿墙起点→终点的距离（米）"},
      "width": {"type": "number"},
      "height": {"type": "number"},
      "sill": {"type": "number", "default": 0.9}
    }
  }
}
```

`add_door` 同上 schema，但 `sill` 默认 0。

### remove_opening

```json
{
  "name": "remove_opening",
  "description": "删窗 / 删门",
  "parameters": {
    "type": "object", "required": ["id"],
    "properties": {"id": {"type": "string"}}
  }
}
```

## Prompt 注入规范（chat-edit.js 服务端）

调 LLM 前，service 给 system prompt 注入：

```
## Current Scene Summary

Room bounds: 5.0m × 4.0m × 2.8m
Objects (21 total):
  - obj_bookshelf (shelf_open) @ [0, 1.65, 1.2] · 书墙
  - obj_desk (desk_standard) @ [-1.4, -0.5, 0.75] · 工作桌
  - obj_chair (chair_standard) @ [-1.4, -1.0, 0.45] · 办公椅
  ...
Walls (3 total): wall_N, wall_W, wall_E
Openings: win_N_1 (window @ wall_N pos_along=2.5)
Lights (3 total): sun_1, pendant_1 (3000K 60W), point_1 (desk)
Materials: WoodFloor, Wall, LightWood, Charcoal, Fabric, Metal, Shade, Screen, Rug

## Available Furniture Types

chair_standard, chair_lounge, sofa_2seat, sofa_3seat, desk_standard, table_coffee,
table_dining, bed_queen, shelf_open, closet_tall, lamp_floor, lamp_pendant
```

LLM 有这些上下文才能正确路由 "删衣柜" → `remove_furniture(id_or_name='closet')` 等。

**节省 token**：不传完整 scene · 只传摘要（id/type/pos/label）· 完整 scene 在客户端持有。

## Few-shot 示例

```
User: 把衣柜往左移 30cm
Assistant: 好，衣柜往左移 30cm。
Tool call: move_furniture({"id_or_name": "obj_closet", "pos_delta": [-0.3, 0, 0]})

User: 把沙发的布换成米色
Assistant: 换成米色。
Tool call: change_material({"target": "obj_sofa", "base_color": "#E8DCC8"})

User: 北墙加个窗户，宽 1.5 米
Assistant: 加了一扇 1.5m 宽的窗在北墙中间。
Tool call: add_window({"wall_id": "wall_N", "pos_along": 2.5, "width": 1.5, "height": 1.5, "sill": 0.9})

User: 把灯调暖一点
Assistant: 把 pendant 调到 2700K 暖光。
Tool call: change_light({"id_or_name": "all", "cct": 2700})

User: 加个能放 3 本书的小书架
Assistant: （识别意图 → 家具库有 shelf_open）放在桌边。
Tool call: add_furniture({"type": "shelf_open", "pos": [-0.5, 1.5, 0.6], "label_zh": "小书架"})
```

## 错误处理

如果 LLM 产生的 tool call 被 ops API 拒绝（如 type 未知），返回消息：

```
{
  "text": "我没法加 bar_chair 这种家具，家具库里没有。可选类型: chair_standard, chair_lounge, sofa_2seat, ...",
  "applied": [],
  "rejected": [{"call": {...}, "reason": "unknown furniture type: bar_chair"}]
}
```

前端显示错误 toast · 用户可以换说法或去家具库扩展（加 GLB + 注册表）。

## 设计决策

1. **fuzzy id_or_name matching**：后端对 object 做模糊匹配（id prefix / label_zh / label_en / type）· LLM 不需严格给 id
2. **delta vs absolute**：`pos_delta` 比 `pos_absolute` 更自然（符合"移 30cm"的语义）· 两者都支持
3. **inline material**：`change_material` 直接给 `base_color` 零门槛 · 服务端自动注册新 material_id
4. **family routing**：LLM 先选 tool，tool 参数映射到 op · 分层减轻 LLM 的认知负担

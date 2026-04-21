# `/api/scene/ops` — Scene 操作统一入口

> **单一变更通道**：chat LLM / floorplan drag / 未来任何 client 都走这一个端点改 scene。

## 端点

```
POST /api/scene/ops
Content-Type: application/json
```

Vercel Edge Function。Session-ephemeral（跟 Phase 1.8 的 `/api/chat-edit` 一致 —— 客户端传当前 scene，服务端算新 scene 返回，不写磁盘）。

## Request

```json
{
  "slug": "01-study-room",
  "scene": { /* 当前 scene · 符合 scene.schema.json */ },
  "ops":   [ /* 1+ 个 op · 数组内按顺序应用 */ ]
}
```

**字段约束**：
- `slug`：必填 · 用于日志 / 审计
- `scene`：必填 · 不合 schema 则 400
- `ops`：必填 · 空数组则 400

## Response

```json
{
  "newScene": { /* 应用所有成功 ops 后的 scene */ },
  "applied":  [ { "op": { ... }, "before": {...}, "after": {...} } ],
  "rejected": [ { "op": { ... }, "reason": "object not found: obj_999" } ],
  "derived": {
    "area_m2": 20.5,
    "perimeter_m": 18.0,
    "object_count": 21,
    "wall_count": 4,
    "light_count": 3
  },
  "errors": []
}
```

**行为**：
- ops 按顺序应用；某 op 失败不中断后续 op（除非该 op 的 `strict: true`）
- `applied[]` 记录成功的 op 及前后状态（方便 undo）
- `rejected[]` 记录失败的 op 及原因
- `derived` 从 `newScene` 重算（墙变了面积变）
- `errors[]` 系统级错误（非 op 级） · 有则该请求整体失败并返回 5xx

## 13 个 Op 定义

### Object 家族（家具 / 装饰 / 设备）

#### `move_object`
```json
{ "op": "move_object", "id": "obj_closet", "pos": [2.0, 0.3, 1.55] }
```
- `pos`：vec3 · 新中心坐标（米）
- 失败条件：`id` 不存在 / `pos` 出 bounds

#### `rotate_object`
```json
{ "op": "rotate_object", "id": "obj_closet", "rotation": [0, 0, 90] }
```
- `rotation`：vec3 · 欧拉度数 [rx, ry, rz]

#### `resize_object`
```json
{ "op": "resize_object", "id": "obj_closet", "size": [0.8, 2.4, 0.45] }
```
- `size`：vec3 · [w, d, h] · 必须 >0

#### `remove_object`
```json
{ "op": "remove_object", "id": "obj_laptop" }
```

#### `add_object`
```json
{
  "op": "add_object",
  "type": "chair_lounge",
  "pos": [1.5, -1.0, 0.4],
  "rotation": [0, 0, 0],
  "size": [0.8, 0.75, 0.8],
  "material_id": "fabric_beige",
  "zone": "reading",
  "label_zh": "阅读椅"
}
```
- `type` 必填 · 家具库 key（见 `data/furniture-library.json`）· 未知 type 降级为 primitive box
- `pos` 必填
- `size` / `material_id` 可选 · 缺则用库 default
- 生成的 `id` 自动：`obj_<type>_<n>`（n = 该 type 已有个数 + 1）

### Wall 家族（墙 + 开洞）

#### `move_wall`
```json
{ "op": "move_wall", "id": "wall_N", "start": [-2.5, 1.0, 0], "end": [2.5, 1.0, 0] }
```
- `start` / `end` vec3 · 起点终点坐标
- 验证：墙长度 >0 · 不能跨 bounds

#### `resize_wall`
```json
{ "op": "resize_wall", "id": "wall_N", "height": 3.2, "thickness": 0.15 }
```
- `height` / `thickness` 可选 · 给哪个改哪个

#### `add_opening`
```json
{
  "op": "add_opening",
  "wall_id": "wall_N",
  "type": "window",
  "pos_along": 2.5,
  "width": 1.5,
  "height": 1.5,
  "sill": 0.9
}
```
- 验证：opening 不能超出墙范围 · 不能重叠
- 生成 `id`：`win_<wall_id>_<n>` 或 `door_<wall_id>_<n>`

#### `remove_opening`
```json
{ "op": "remove_opening", "id": "win_N_1" }
```

### Light 家族

#### `add_light`
```json
{
  "op": "add_light",
  "type": "pendant",
  "pos": [0, 0, 2.5],
  "cct": 3000,
  "power": 60
}
```
- `type` 必填 · `color` 可由 `cct` 自动算

#### `change_light`
```json
{ "op": "change_light", "id": "pendant_1", "cct": 2700, "power": 80 }
```
- 给哪个字段改哪个

#### `remove_light`
```json
{ "op": "remove_light", "id": "pendant_1" }
```

### Material 家族

#### `change_material`
```json
{ "op": "change_material", "target": "obj_closet", "material_id": "oak_wood" }
```
```json
{ "op": "change_material", "target": "wall_N", "material_id": "wall_paint_cream" }
```
```json
{ "op": "change_material", "target": "floor", "material_id": "oak_wood" }
```
- `target` = object_id | wall_id | `"floor"` | `"ceiling"`
- 也可 inline 创建新材质：
  ```json
  { "op": "change_material", "target": "wall_N",
    "material": { "base_color": "#E8DCC8", "roughness": 0.9 } }
  ```
  此时自动生成 `material_id = mat_inline_<n>` 并加入 `scene.materials`

## Derived 重算

每次成功 ops 应用后 · 算：
- `area_m2`：从 walls 围出的闭合多边形计算（用 `polygon_area`）
- `perimeter_m`：walls 总长度
- `object_count` / `wall_count` / `light_count`

这些 derived 回传给前端，前端 dispatch 时同步到 `data.project.area` / `data.derived.*`，触发 BOQ / Energy 重算（复用 Phase 1.8 的 derived compute）。

## 错误码

| 状态 | 含义 |
|---|---|
| 400 | body 不合法 · scene schema 不过 · ops 空 |
| 404 | slug 不存在（仅当 audit log 要求查时）|
| 500 | 内部错误 · 见 `errors[]` |

## 审计日志（可选 · Phase 3）

每次成功应用的 ops 写 `timeline[]` 条目 · 客户端选择是否 dispatch。

## 设计决策

1. **无状态**：scene 由客户端传入，服务端不维护会话 → 多 client 共享无污染
2. **原子性**：ops 按顺序应用 · 单 op 失败不阻塞（除非 strict）· 便于 chat 部分成功
3. **幂等**：同样的 ops + 同样的 scene 永远产出同样的 newScene
4. **可审计**：applied[].before/after 可支持撤销 · rejected[] 让 UI 提示用户

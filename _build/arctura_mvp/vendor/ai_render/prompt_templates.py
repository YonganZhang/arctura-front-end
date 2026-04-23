"""
P4 AI Render — Prompt 模板库
根据 brief.json 的 scene_type / style 自动选择最佳 prompt
"""

# 通用质量后缀（所有 prompt 追加）
QUALITY_SUFFIX = (
    "professional interior design photography, "
    "realistic materials and textures, detailed furniture, "
    "8k uhd, high quality, architectural digest style, "
    "warm natural lighting, ambient occlusion"
)

NEGATIVE_PROMPT = (
    "low quality, blurry, cartoon, anime, sketch, wireframe, "
    "low resolution, oversaturated, distorted, deformed, "
    "text, watermark, logo, ugly, duplicate, morbid"
)

# 按场景类型的 prompt 模板
SCENE_PROMPTS = {
    # --- 餐饮 ---
    "coffee-shop": (
        "modern specialty coffee shop interior, espresso bar with wood counter, "
        "pendant lights, exposed brick, cozy seating area, potted plants, "
        "warm ambient lighting, latte art display"
    ),
    "restaurant": (
        "upscale modern restaurant interior, fine dining atmosphere, "
        "elegant table settings, mood lighting, wine display, "
        "textured wall panels, plush seating, warm tones"
    ),
    "bistro": (
        "charming European bistro interior, rustic wooden tables, "
        "ambient pendant lighting, chalkboard menu, wine bottles, "
        "cozy intimate atmosphere, vintage details"
    ),
    "bakery": (
        "artisan bakery and cafe interior, display cases with pastries, "
        "warm wood tones, pendant lights, subway tiles, "
        "flour-dusted counter, cozy cafe seating"
    ),

    # --- 办公 ---
    "office": (
        "modern corporate office interior, ergonomic workstations, "
        "glass partitions, task lighting, clean minimal design, "
        "professional atmosphere, indoor plants"
    ),
    "coworking": (
        "trendy coworking space, hot desks and private pods, "
        "industrial-modern style, exposed ceiling, colorful accents, "
        "collaborative zones, phone booths, green walls"
    ),
    "conference-room": (
        "modern executive conference room, large meeting table, "
        "ergonomic chairs, presentation screen, acoustic panels, "
        "professional lighting, glass walls"
    ),
    "startup-office": (
        "modern tech startup office, open plan workspace, "
        "standing desks, breakout areas, whiteboards, "
        "vibrant accent colors, casual meeting zones"
    ),

    # --- 零售 ---
    "bookstore": (
        "cozy independent bookstore interior, floor-to-ceiling shelves, "
        "reading nooks, warm wood tones, soft lighting, "
        "comfortable armchairs, literary atmosphere"
    ),
    "gallery": (
        "contemporary art gallery interior, white walls, "
        "track lighting, polished concrete floor, "
        "minimalist display, high ceilings, clean lines"
    ),
    "retail": (
        "modern boutique retail store interior, display shelving, "
        "accent lighting, clean merchandising, "
        "premium materials, brand-focused design"
    ),
    "floral": (
        "elegant floral atelier interior, flower display coolers, "
        "rustic wood work tables, hanging dried flowers, "
        "natural light, botanical aesthetic, greenery"
    ),

    # --- 健康 & 健身 ---
    "dental-clinic": (
        "modern dental clinic interior, treatment room, "
        "clinical white with calming accent colors, "
        "professional equipment, soothing atmosphere, clean design"
    ),
    "clinic": (
        "modern medical clinic interior, reception and waiting area, "
        "calming colors, comfortable seating, clean surfaces, "
        "professional yet welcoming atmosphere"
    ),
    "fitness": (
        "modern fitness studio interior, workout equipment, "
        "rubber flooring, mirror walls, dynamic lighting, "
        "motivational atmosphere, industrial accents"
    ),
    "wellness": (
        "luxury spa and wellness center interior, treatment rooms, "
        "natural materials, soft lighting, zen atmosphere, "
        "water features, stone and wood textures"
    ),

    # --- 教育 & 儿童 ---
    "daycare": (
        "colorful children daycare center interior, play areas, "
        "rounded furniture, bright primary colors, safe design, "
        "reading corner, activity zones, cheerful atmosphere"
    ),
    "study-room": (
        "modern study room interior, individual desks, bookshelves, "
        "quiet focused atmosphere, task lighting, "
        "organized layout, warm neutral tones"
    ),
    "study-hall": (
        "university study hall interior, long reading tables, "
        "library atmosphere, warm wood, pendant lights, "
        "quiet study zones, power outlets, bookshelves"
    ),

    # --- 住宅 ---
    "living-room": (
        "modern luxury living room interior, comfortable sofa, "
        "coffee table, area rug, accent lighting, artwork, "
        "warm neutral palette, indoor plants, cozy atmosphere"
    ),
    "bedroom": (
        "elegant modern bedroom interior, king bed with headboard, "
        "bedside tables, soft lighting, textured bedding, "
        "curtains, warm peaceful atmosphere"
    ),
    "elderly-home": (
        "accessible elderly-friendly home interior, grab bars, "
        "wide pathways, comfortable recliner, warm lighting, "
        "non-slip flooring, safe cozy atmosphere"
    ),

    # --- 特殊 ---
    "recording-studio": (
        "professional recording studio interior, acoustic panels, "
        "mixing console, studio monitors, sound diffusers, "
        "mood lighting, professional audio equipment"
    ),
    "pool": (
        "luxury indoor swimming pool interior, turquoise water, "
        "ambient underwater lighting, loungers, "
        "tropical plants, spa atmosphere, natural stone"
    ),
    "tea-room": (
        "zen Japanese tea room interior, tatami mats, "
        "low wooden table, shoji screens, ikebana arrangement, "
        "natural materials, serene minimalist atmosphere"
    ),
    "hair-salon": (
        "modern hair salon interior, styling stations with mirrors, "
        "salon chairs, product displays, glamorous lighting, "
        "marble counters, chic contemporary design"
    ),
}

# 风格修饰词（叠加到场景 prompt 上）
STYLE_MODIFIERS = {
    "japanese": "Japanese-inspired design, wabi-sabi aesthetic, natural wood, paper screens, ",
    "scandinavian": "Scandinavian hygge style, light wood, white walls, minimal, cozy textiles, ",
    "industrial": "industrial loft style, exposed brick, metal pipes, Edison bulbs, concrete, ",
    "minimalist": "ultra-minimalist design, clean lines, monochrome palette, negative space, ",
    "luxury": "luxury high-end design, marble, gold accents, velvet upholstery, crystal, ",
    "vintage": "vintage retro design, mid-century modern furniture, warm tones, nostalgic, ",
    "tropical": "tropical resort style, rattan furniture, palm leaves, natural textures, ",
    "zen": "zen minimalist style, natural materials, stone, bamboo, water elements, ",
    "modern": "contemporary modern design, clean geometric forms, neutral palette, ",
    "rustic": "rustic farmhouse style, reclaimed wood, natural stone, warm textures, ",
}


def get_prompt_for_brief(brief: dict) -> tuple[str, str]:
    """从 brief.json 生成 (positive_prompt, negative_prompt)"""
    scene_type = brief.get("scene_type", "").lower().replace(" ", "-")
    style = brief.get("style", "modern").lower()

    # 匹配场景
    scene_prompt = SCENE_PROMPTS.get(scene_type, "")
    if not scene_prompt:
        # 模糊匹配
        for key, val in SCENE_PROMPTS.items():
            if key in scene_type or scene_type in key:
                scene_prompt = val
                break
    if not scene_prompt:
        scene_prompt = (
            "modern interior design, detailed furniture and materials, "
            "warm ambient lighting, realistic textures"
        )

    # 叠加风格
    style_mod = ""
    for key, mod in STYLE_MODIFIERS.items():
        if key in style:
            style_mod = mod
            break

    positive = f"{style_mod}{scene_prompt}, {QUALITY_SUFFIX}"
    return positive, NEGATIVE_PROMPT


def get_prompt_for_type(scene_type: str, style: str = "modern") -> tuple[str, str]:
    """直接用场景类型 + 风格获取 prompt"""
    return get_prompt_for_brief({"scene_type": scene_type, "style": style})

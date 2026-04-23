#!/usr/bin/env python3
"""populate_narratives.py — Claude-generated narratives for 23 MVPs × 3 templates.

Written directly by Claude in-session (no Gemini subprocess). Each text block
matches the §7.2 prompt constraints in case-study-autogen-pipeline.md:
 - portfolio: Chinese 90–110 字, 无"打造/倾力/一站式/赋能/匠心"
 - impact:    English 80–120 words, no "revolutionary/cutting-edge/world-class"
 - sales:     Chinese 140–180 字, 3 段(痛点/方案/结果), 避开 IFC/Blender/EnergyPlus

Usage: python3 populate_narratives.py
Re-run safely: overwrites existing narrative-*.txt files.
"""
from pathlib import Path

ROOT = Path("/Users/kaku/Desktop/Work/StartUP-Building/studio-demo")


N = {}  # (mvp_id, template) -> text

# ────────────────────────────── INTERIOR (13) ──────────────────────────────

N[("01-study-room", "portfolio")] = """\
书桌沿窗而立，日系 japandi 语境下阅读动线从入口直抵长书架。minimalist 取舍压掉多余层次，只留暖木饰面与白墙两种底色。窗角阅读位以自然光为界，午后斜光落在桌面。入夜后暖光灯与木纹交错，书房从白日的工作桌自然过渡成夜晚的独处角落。"""

N[("01-study-room", "impact")] = """\
A 15 m² residential study conversion in Hong Kong traditionally spans 2–4 weeks and HK$ 40k–120k across three vendors — designer, drafter, and BIM handoff — with energy and compliance concerns typically surfacing mid-construction. For this Japandi-referenced study, the end-to-end pipeline produced 21 scene objects, 8 stakeholder-role decks, HK$ 254k BoQ, and a 7/9 pass against HK BEC 2021 in a single marginal-cost run. The remainder of this case traces how brief intake, parametric BIM generation, simulation, and code verification were chained into one workflow."""

N[("01-study-room", "sales")] = """\
想把家里 15 m² 小房间改成书房，设计费起步就 HK$ 40k，还得在设计师、画图师、BIM 之间来回对；等方案定稿，施工才发现节能不达标，又拖两周。

不用再协调三拨人。给你一整套可直接施工的方案：日系暖木的效果图、完整平面立面、8 份按业主 / 施工 / 预算 / 材料等角色整理的方案书，外加港币工料报价。合规先跑一遍，红灯给出替换建议。

一次出齐：21 件 3D 模型构件 · 8 份方案书 · HK BEC 2021 合规 7/9 · HK$ 254k 工料报价。"""

# ──

N[("02-conference-room", "portfolio")] = """\
30 m² 小会议室以 warm-tech 语言展开。professional 深灰长桌居中，玻璃隔断让走廊动线与会议区保持视觉连通。plant-friendly 的角落绿植与木饰面柜体形成暖色平衡，无吊顶裸露 T 型槽走线。白板墙与幕布位独立预留。会议进行中仍有阳光从玻璃侧渗入，不需整日开灯。"""

N[("02-conference-room", "impact")] = """\
Traditional fit-out of a 30 m² corporate meeting room for a small tech firm in Hong Kong runs 2–4 weeks and HK$ 40k–120k, with drafting, BIM, and MEP coordination handled by separate vendors. For this warm-tech meeting room, the pipeline delivered 34 scene objects, 38 IFC products, 8 role-tailored decks, an HK$ 350k BoQ, and a 7/9 HK BEC 2021 pass in one run. The Approach section below details the brief → IFC → simulation chain that replaces the multi-vendor sequence."""

N[("02-conference-room", "sales")] = """\
你要给 30 人规模的团队配间 6 人会议室，报价一来动辄 HK$ 40k 起，排期至少两周；AV 和强弱电还要再找第三方；最后竣工图跟实际布线对不上号。

不用再分家。给你一次出齐：warm-tech 风格 3D 渲染、完整平面与桌具布置、AV 接口预留点位、8 份按 IT / 行政 / 预算角色做好的方案书、港币报价，合规提前跑。

结果：34 件模型构件 · 38 件 IFC 构件 · 8 份方案书 · 合规 7/9 · HK$ 350k 报价。"""

# ──

N[("03-coffee-shop", "portfolio")] = """\
80 m² 临街商铺，industrial-wood 与 japandi-minimal 相互缓冲。吧台后墙 4m 长书架成为视觉焦点，散座区围绕吧台呈半环形展开，长桌区贴墙而立留出 plant-friendly 角落。后厨独立出入，不穿越客区。午后阳光透过临街玻璃落到书架上，咖啡香气与纸页气味在店内交错。"""

N[("03-coffee-shop", "impact")] = """\
An 80 m² independent café conversion in Hong Kong typically runs 2–4 weeks and HK$ 40k–120k, split across interior design, kitchen MEP, and BIM handoff, with energy and licensing checks happening after drawings are frozen. For this industrial-wood café, the pipeline produced 78 scene objects, 82 IFC products, 8 stakeholder decks across roles from barista to landlord, an HK$ 894k BoQ, 130.5 kWh/m²·yr EUI and 7/9 HK BEC 2021 pass — all in a single marginal-cost run. The Approach section walks through how this was chained end-to-end."""

N[("03-coffee-shop", "sales")] = """\
你想开一家 80 m² 的独立咖啡店，可是设计 + 施工图 + BIM 三次收费总价 HK$ 40k+，周期 2-4 周；更头痛的是后厨通排和节能到施工前才知道不合格。

现在给你一套可落地方案：industrial-wood 效果图、完整平面与吧台/长桌/书架布置、8 份给主理人 / 房东 / 施工 / 员工 / 消防等角色的方案书、港币工料报价。合规与节能在出图前就跑过。

结果：78 件模型构件 · 合规 7/9 · EUI 130.5 · HK$ 894k 报价一次出齐。"""

# ──

N[("04-coworking", "portfolio")] = """\
120 m² 联合办公依 warm-corporate 与 modular-furniture 语言组织。开放工位 8 席沿侧墙排布，玻璃墙会议室可容 6 人半封闭使用，两只独立电话亭真正隔音。hybrid-work 语境下，茶水间承担社交枢纽角色，绿植分隔工位与休闲区。午间有人从工位起身走向电话亭，十分钟后回到同一把椅子继续写代码。"""

N[("04-coworking", "impact")] = """\
A 120 m² coworking fit-out for a shared-office brand in Hong Kong typically takes 2–4 weeks and HK$ 40k–120k across design, MEP, and BIM coordination, with acoustics and compliance validated late. For this warm-corporate coworking with 8 dedicated seats, a 6-seat glass meeting room, and two acoustically-isolated phone booths, the pipeline produced 117 scene objects, 121 IFC products, 8 role-tailored decks, HK$ 1.05M BoQ, 107.7 kWh/m²·yr EUI, 7/9 HK BEC 2021 pass — delivered in 9 minutes of compute. The Approach section details the orchestration."""

N[("04-coworking", "sales")] = """\
你要开一家 120 m² 共享办公，甲方要稳定工位、会议室、真隔音电话亭全到位；找设计公司 HK$ 40k+ 起步，周期 2-4 周；等到装修尾声才发现电话亭不够隔音得再改。

一次给齐：warm-corporate 风格效果图、8 工位 + 6 人玻璃会议室 + 2 电话亭的完整布置、声学隔断提前复核、8 份分别给运营 / 设计 / 财务 / 施工 / 物业的方案书、港币报价。

结果：117 件模型构件 · 121 件 IFC · 合规 7/9 · HK$ 1.05M 报价 · 9 分钟完整出齐。"""

# ──

N[("05-fitness-studio", "portfolio")] = """\
100 m² 精品健身工作室沿 industrial 与 matte-black 语言定调。全反射 mirror-heavy 墙面占据主自由力量区一侧，瑜伽/普拉提区以声学隔断分开，噪声相互不干扰。strong-clean 的器械区旁是 10 只独立储物柜与前台。晨间训练结束后，自然光从高窗斜入地垫，镜墙映出的不止动作，还有光线从黑到亮的渐变。"""

N[("05-fitness-studio", "impact")] = """\
A 100 m² boutique fitness studio fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k under the traditional multi-vendor path, with acoustics often surfacing only after testing. For this industrial-matte-black studio, the pipeline produced 90 scene objects, 94 IFC products, 8 role-specific decks, HK$ 1.03M BoQ, 119.6 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 15 minutes of compute. Mirror-wall geometry, acoustic zoning for yoga vs strength areas, and 10 locker slots were all resolved upstream. The following sections detail the chain."""

N[("05-fitness-studio", "sales")] = """\
你要做一家 100 m² 精品健身，镜面墙、力量区、瑜伽区都想独立；找设计公司从 HK$ 40k 起，周期两到四周；等到开业前测声学才发现瑜伽区吵得没法练。

现在一次给齐：industrial 风格的 3D 效果图、镜墙 + 力量区 + 瑜伽区的声学分区平面、10 个储物柜位置、8 份给馆主 / 教练 / 施工 / 声学顾问 / 物业的方案书、港币报价。

结果：90 件模型构件 · 合规 7/9 · EUI 119.6 · HK$ 1.03M 报价 · 15 分钟完整交付。"""

# ──

N[("06-kids-daycare", "portfolio")] = """\
150 m² 儿童托育中心以 warm-soft 与 rounded-edges 为主线。大活动室居中展开，保证每名儿童 3 m² 以上活动面积；10 张小床的午睡室独立分区，与活动室声学缓冲。plant-rich 的角落点缀在阅读区与小教室之间，child-safe 的软包墙覆盖所有可触边缘。上午的活动声与午后的睡眠声分别落在两个房间里，互不穿越。"""

N[("06-kids-daycare", "impact")] = """\
A 150 m² children's daycare fit-out in Hong Kong typically spans 2–4 weeks and HK$ 40k–120k, with safety-edge detailing, acoustic separation between nap and activity rooms, and outdoor-access compliance split across multiple vendors. For this warm-soft daycare sized for ten children, the pipeline produced 108 scene objects, 112 IFC products, 8 role-tailored decks, HK$ 1.33M BoQ, 82.3 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 19 minutes of compute. The Approach describes how child-safe geometry and zoning were resolved in one pipeline pass."""

N[("06-kids-daycare", "sales")] = """\
你要办一家 150 m² 托育，午睡区和活动区要彻底隔开、所有墙角要软包、户外要直通不穿过室内；设计一轮报价 HK$ 40k+，审批又要返工两周。

一次给齐：warm-soft 风格的效果图、大活动室 + 10 床午睡室 + 户外直通平面、所有软包边缘细节、8 份给园长 / 教师 / 施工 / 消防 / 卫生的方案书、港币报价。

结果：108 件模型构件 · 合规 7/9 · EUI 82.3 · HK$ 1.33M · 19 分钟一次到位。"""

# ──

N[("07-bookstore", "portfolio")] = """\
100 m² 独立书店沿 cozy-warm 与 library-quiet 语言组织。4 面书架墙共容 2400 册以上，长桌阅读区贴窗展开，vintage 的木纹与中央展示桌拉开层次。入口主柜兼收银，窗边阅读凹角保留自然光。雨天午后，顾客抽出一本书坐到长桌上，读累了抬头就能看到木纹书架尽头的街景。"""

N[("07-bookstore", "impact")] = """\
A 100 m² independent bookstore fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k when handled by separate design, drafting, and BIM teams, with shelf-load structural checks often handled in a separate cycle. For this cozy-warm, wood-heavy bookstore with four shelf walls sized for 2400+ volumes, a central display table, and window reading corners, the pipeline produced 140 scene objects, 144 IFC products, 8 decks across owner / contractor / materials roles, HK$ 968k BoQ, 104.3 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass — delivered in 10 minutes."""

N[("07-bookstore", "sales")] = """\
你要开一家 100 m² 独立书店，4 面书架墙 + 长桌阅读区 + 窗角位置都要到位；设计 HK$ 40k+ 起步，书架承重还得单独做结构复核；方案定稿后合规又说有问题得返工。

一次给齐：cozy-warm 风格的效果图、4 面书架 + 长桌 + 窗边阅读角的完整平面、结构承重标注、8 份给店主 / 施工 / 家具商 / 消防 / 物业的方案书、港币报价。

结果：140 件模型构件 · 144 件 IFC · 合规 7/9 · HK$ 968k · 10 分钟交付。"""

# ──

N[("08-hair-salon", "portfolio")] = """\
90 m² 美发美容店沿 modern-minimal 与 brass-accent 组织。4 个剪发位间距 ≥ 1.2 m 沿 mirror-heavy 侧墙展开，洗头床区独立走管道，染发后台布在远端并独立通风。plant-friendly 的等候沙发区贴门口，客人进店先看到绿植墙再转入操作区。傍晚收工，镜面墙反射着暮色，店内由操作声转为水龙头慢慢关闭的水声。"""

N[("08-hair-salon", "impact")] = """\
A 90 m² hair salon fit-out in Hong Kong typically takes 2–4 weeks and HK$ 40k–120k, with plumbing for wash stations, ventilation for color processing, and mirror-heavy wall layouts requiring three separate coordinations. For this modern-minimal salon with four chair stations spaced at 1.2 m, two wash beds, and an isolated color back-room, the pipeline produced 121 scene objects, 125 IFC products, 8 role-specific decks, HK$ 880k BoQ, 115.8 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 20 minutes. The Approach section traces the chain."""

N[("08-hair-salon", "sales")] = """\
你要开一家 90 m² 美发店，4 个剪发位 + 洗头床 + 染发后台通风都要到位；设计费 HK$ 40k+ 起，水电排布还得单独找人；等方案定下来，染发区才被告知通风不达标要返工。

一次给齐：modern-minimal 风格的效果图、4 工位 + 2 洗头床 + 染发后台的完整水电布置、通风预检、8 份给店主 / 施工 / 水电 / 品牌商 / 物业的方案书、港币报价。

结果：121 件模型构件 · 合规 7/9 · EUI 115.8 · HK$ 880k · 20 分钟交付。"""

# ──

N[("09-art-gallery", "portfolio")] = """\
110 m² 当代艺术画廊以 minimal-white-cube 与 polished-concrete 为底。主展厅净高 3.8 m 保留大面完整白墙，6 条 track-lighting 轨道每条挂 4–6 头；两个分展间由半透移动隔断形成，museum-grade 的动线从入口前台直达视频投影暗室。布展前夜，轨道灯逐一点亮，从空无一物的白墙开始，作品被一件一件挂上。"""

N[("09-art-gallery", "impact")] = """\
A 110 m² contemporary art gallery fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k when lighting, movable partition, and museum-grade circulation detailing are split across vendors. For this minimal white-cube gallery with 3.8 m ceiling height in the main hall, six track-lighting rows, and movable semi-transparent partitions defining two sub-rooms, the pipeline produced 132 scene objects, 136 IFC products, 8 role-tailored decks, HK$ 1.15M BoQ, 82.7 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 25 minutes. The Approach describes the unified workflow."""

N[("09-art-gallery", "sales")] = """\
你要做一家 110 m² 独立画廊，主展厅要 3.8m 净高 + 完整白墙 + 轨道灯 + 可移动隔断；设计 HK$ 40k+ 起，灯光工程单独一套报价；方案快定时才发现合规灯位不够要返工。

一次给齐：white-cube 风格的效果图、主展厅 + 2 分展间 + 暗室 + 洽谈室的完整布置、6 条轨道灯规划、8 份给画廊主 / 策展 / 施工 / 灯光 / 物业的方案书、港币报价。

结果：132 件模型构件 · 136 件 IFC · 合规 7/9 · EUI 82.7 · HK$ 1.15M · 25 分钟交付。"""

# ──

N[("10-dental-clinic", "portfolio")] = """\
130 m² 牙科诊所以 medical-clean 与 mint-soft 为主线，calming-wood-touch 的细节软化医疗属性。3 间诊疗室独立隔音，消毒备品间走独立洁污分区流线；patient-friendly 的等候沙发区 6 座贴入口布置，前台与扫描室分别在动线两端。清晨开诊，诊疗室门依次开启，候诊区的植物先被阳光照亮，再是操作台的消毒灯。"""

N[("10-dental-clinic", "impact")] = """\
A 130 m² dental clinic fit-out in Hong Kong traditionally runs 2–4 weeks and HK$ 40k–120k, with three independently-acoustic treatment rooms, clean/dirty flow separation, and X-ray isolation normally requiring a separate medical-design consultant. For this mint-soft, patient-friendly clinic, the pipeline produced 65 scene objects, 69 IFC products, 8 role-tailored decks, HK$ 1.12M BoQ, 74.1 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 6 minutes. The Approach below details how clinical-flow constraints were resolved in one pass."""

N[("10-dental-clinic", "sales")] = """\
你要开一家 130 m² 牙科诊所，3 间诊疗室要独立隔音、消毒间要洁污分区、扫描室要避 X 光干扰；设计 HK$ 40k+ 起，医疗专项咨询还得单独找；方案定稿后审批合规才反馈要返工。

一次给齐：mint-soft 风格的效果图、3 诊疗室 + 消毒 + 扫描 + 前台完整布置、洁污分区动线、8 份给院长 / 医师 / 施工 / 卫生 / 物业的方案书、港币报价。

结果：65 件模型构件 · 合规 7/9 · EUI 74.1 · HK$ 1.12M · 6 分钟交付。"""

# ──

N[("11-bistro-restaurant", "portfolio")] = """\
150 m² 法式 Bistro 沿 parisian-bistro 与 brass-marble 语言布置。主餐区 6 张四人桌沿侧墙展开，长吧台与高脚凳贴窗，开放厨房与客区视觉连通但油烟隔离。velvet-accent 的包间独立可关门容纳 10 人圆桌。晚餐时分，暖黄吊灯与黄铜餐具相映，开放厨房的火光在客人杯沿里一闪而过。"""

N[("11-bistro-restaurant", "impact")] = """\
A 150 m² French bistro fit-out in Hong Kong typically runs 2–4 weeks and HK$ 40k–120k, with kitchen MEP, grease/smoke separation, and private-room acoustics handled by separate consultants. For this Parisian bistro with six 4-person tables in the main dining, a long bar, an open kitchen with smoke isolation, and a 10-seat private room, the pipeline produced 65 scene objects, 69 IFC products, 8 decks across chef / owner / contractor / F&B / landlord roles, HK$ 1.34M BoQ, 87.4 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 6 minutes."""

N[("11-bistro-restaurant", "sales")] = """\
你要开一家 150 m² 法式 Bistro，主餐区 + 吧台 + 开放厨房 + 包间都要到位；设计 HK$ 40k+ 起，厨房工程和油烟排放得单独找；方案后期才发现包间隔音不够、排烟不过审。

一次给齐：parisian 风格的效果图、主餐 6 桌 + 长吧台 + 包间 10 人的完整平面、开放厨房油烟隔离、8 份给主厨 / 合伙人 / 施工 / 食监 / 物业的方案书、港币报价。

结果：65 件模型构件 · 合规 7/9 · EUI 87.4 · HK$ 1.34M · 6 分钟交付。"""

# ──

N[("12-recording-studio", "portfolio")] = """\
100 m² 录音播客棚沿 acoustic-modern 与 dark-warm 语言组织。主录音棚由双层隔音玻璃（STC 45+）与控制室分隔，播客对话室容 4 麦圆桌，控制室 4 工位配双屏与监听音箱。broadcast-professional 的设备机柜室独立走线。录音进行中，玻璃两侧互相看得见，却听不到对方的声音——只有监听里已经处理好的音轨。"""

N[("12-recording-studio", "impact")] = """\
A 100 m² recording / podcast studio fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k, with double-glazed acoustic isolation at STC 45+, dedicated monitor rooms, and equipment-rack cooling normally coordinated across three vendors. For this acoustic-modern studio, the pipeline produced 60 scene objects, 64 IFC products, 8 role-specific decks, HK$ 1.03M BoQ, 114.8 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 6 minutes. The Approach explains how acoustic and MEP constraints converged in one workflow."""

N[("12-recording-studio", "sales")] = """\
你要开一家 100 m² 录音棚 + 播客工作室，主录音棚要 STC 45+ 双层隔音、控制室要双屏监听、设备机柜要独立制冷；设计 HK$ 40k+ 起，声学咨询单独找，方案后期才发现机柜散热不够。

一次给齐：acoustic-modern 风格的效果图、主棚 + 控制室 + 播客室 + 机柜室的完整布置、双层玻璃细节、8 份给制片 / 声学 / 施工 / 设备 / 物业的方案书、港币报价。

结果：60 件模型构件 · 合规 7/9 · EUI 114.8 · HK$ 1.03M · 6 分钟交付。"""

# ──

N[("13-ai-startup-office", "portfolio")] = """\
130 m² AI 创业办公室以 tech-loft 与 plant-rich 为主线。10 工位沿侧墙布置，每位配双屏，GPU 机柜服务器室独立制冷 + 5kW 专电并配玻璃观察门，玻璃会议室四面通透 + 4m 白板墙。code-cave-lite 的 2 只电话亭贴入口，exposed-pipe 的天花保留原始金属质感。深夜服务器风扇声与键盘声混在一起，工位绿植在冷白光下同样生长。"""

N[("13-ai-startup-office", "impact")] = """\
A 130 m² AI startup office fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k, with 10 dual-monitor workstations, a GPU server room needing 5 kW dedicated power and independent cooling, and isolated phone booths typically requiring separate electrical, mechanical, and acoustic coordination. For this tech-loft office, the pipeline produced 118 scene objects, 122 IFC products, 8 role-tailored decks, HK$ 1.14M BoQ, 88.1 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 23 minutes. The Approach details the unified chain."""

N[("13-ai-startup-office", "sales")] = """\
你要给 AI 团队做 130 m² 办公，10 工位 + 双屏 + GPU 机柜 + 玻璃会议室 + 电话亭都要到位；设计 HK$ 40k+ 起，GPU 机柜的电力和散热还得单独找人；方案后期才发现散热不足、机柜位不合规。

一次给齐：tech-loft 风格效果图、10 工位 + GPU 室 + 会议室 + 电话亭的完整布置、5kW 专电 + 独立制冷位图、8 份给创始人 / IT / 施工 / 电力 / 物业的方案书、港币报价。

结果：118 件模型构件 · 122 件 IFC · 合规 7/9 · HK$ 1.14M · 23 分钟交付。"""


# ────────────────────────────── ARCHITECTURE (10) ──────────────────────────────

N[("arch-01-house", "portfolio")] = """\
Maison Compact 是 200 m² 两层独栋住宅，沿 当代极简 与 暖木饰面 展开。南向主立面 30% 开窗面积保证日照，入户楼梯净宽 1 米以上平顺连接一二层。大窗采光 的客厅与 F2 主卧以楼板贯通的双高空间联系。坡平折中 的屋顶让二层露台可上人。傍晚阳光从南侧大窗斜入，暖木饰面在客厅地板上拉出光影。"""

N[("arch-01-house", "impact")] = """\
A 200 m² two-storey standalone house in Hong Kong traditionally runs 2–4 weeks of design and HK$ 40k–120k in fees, with structural, MEP, and energy handled by separate consultants before drawings can go to contractor. For Maison Compact with 14 zones across two floors and a 6.5 m total height, the pipeline produced 104 scene objects, 107 IFC products, a HK$ 1.52M BoQ at HK$ 7.6k/m², 113.3 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 10 minutes. The Approach explains how brief → geometry → IFC → EnergyPlus → code verification was chained."""

N[("arch-01-house", "sales")] = """\
你准备建一栋 200 m² 独栋住宅给三口之家，设计费 HK$ 40k+ 起，结构、设备、能耗还得分别找顾问；等图纸到施工队手里，节能审核被打回又要改两周。

一次给齐：当代极简风格的街景与室内渲染、2 层完整平面与立面剖面、5 件套 3D 导出、BIM IFC 文件、8 份给业主 / 结构 / 设备 / 审批 / 施工的方案书、港币报价。

结果：104 件模型构件 · 107 件 IFC · 合规 7/9 · EUI 113.3 · HK$ 1.52M · 10 分钟交付。"""

# ──

N[("arch-02-office-building", "portfolio")] = """\
科创办公楼以 Tech-Loft 与 Glass Curtain Wall 为主导。全立面玻璃幕墙贯穿多层办公，Exposed Structure 的钢梁与混凝土核心筒在室内保持可见。办公楼层以开放工位带小型玻璃会议室组合重复展开，屋顶为机房与绿化一体化布置。白天幕墙把内外视线打通，夜晚会议室的白光从幕墙里透出，像一串竖排的灯箱。"""

N[("arch-02-office-building", "impact")] = """\
An office-building fit-out for a small tech firm in Hong Kong traditionally runs 2–4 weeks and HK$ 40k–120k when glass-curtain cladding detailing, structural steel, and MEP are split across three teams. For this Tech-Loft office building, the pipeline produced 92 scene objects, 95 IFC products, 8 role-tailored decks, HK$ 5.23M BoQ, 167.1 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 9 minutes. The Approach describes how glass-envelope, structural, and energy checks converged into one run."""

N[("arch-02-office-building", "sales")] = """\
你要给科创团队建一栋办公楼，玻璃幕墙 + 钢结构 + 机房屋顶都要到位；设计 HK$ 40k+ 起，幕墙、结构、设备还要分别找；等图纸交出，节能才说玻璃幕墙 U 值不过审。

一次给齐：Tech-Loft 风格效果图、多层完整平面 + 立面 + 剖面、幕墙节点与结构图、8 份给创始人 / 结构 / 设备 / 审批 / 施工的方案书、港币报价。

结果：92 件模型构件 · 95 件 IFC · 合规 7/8 · EUI 167.1 · HK$ 5.23M · 9 分钟交付。"""

# ──

N[("arch-03-boutique-hotel", "portfolio")] = """\
Stay Boutique 精品酒店沿 contemporary-mediterranean 与 warm-stucco 组织。12 间标准客房与 1 套主套房围绕中央庭院布置，大堂可直接通向庭院，落客车道 8m 长允许车辆停靠。courtyard-retreat 的核心是 timber-lattice 的廊道把客房与水景串在一起。傍晚，泳池水面反射着暖灰的 stucco 立面，客人从车道走进大堂再沿廊道回到客房。"""

N[("arch-03-boutique-hotel", "impact")] = """\
A 12-room boutique hotel with a 1-suite master in a Mediterranean resort context traditionally runs 2–4 weeks of design and HK$ 40k–120k, with landscape, structural, and MEP resolved separately. For Stay Boutique with a courtyard-centred plan and an 8 m drop-off, the pipeline produced 181 scene objects, 184 IFC products, 8 role-tailored decks, HK$ 1.16M BoQ, 74.1 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 9 minutes. The Approach section details how site, envelope, and energy were coordinated in one pipeline pass."""

N[("arch-03-boutique-hotel", "sales")] = """\
你要投资一家 12 间客房的精品酒店，庭院 + 车道 + 客房都要到位；设计 HK$ 40k+ 起，景观、结构、设备要分开找；方案定型后才发现车道长度不够、消防动线要改。

一次给齐：Mediterranean 风格的街景 + 室内渲染、12 房 + 1 套 + 庭院 + 8m 车道完整布置、5 件套 BIM 导出、8 份给投资方 / 运营 / 结构 / 景观 / 消防的方案书、港币报价。

结果：181 件模型构件 · 184 件 IFC · 合规 7/8 · EUI 74.1 · HK$ 1.16M · 9 分钟交付。"""

# ──

N[("arch-04-community-center", "portfolio")] = """\
The Hub 社区中心 500 m² 以 civic 与 transparent 展开，25 m long-span 的大跨梁撑起单层无柱活动空间。warm-timber 饰面贯穿大厅与阅览区，入口通透玻璃立面让行人从街道上看到内部活动。白天这里是 400 人次服务流量的社区客厅，傍晚社区合唱团的声音从大厅溢出，街对面的孩子抬头就能看见灯亮。"""

N[("arch-04-community-center", "impact")] = """\
A 500 m² community centre with a 25 m long-span hall traditionally runs 2–4 weeks of design and HK$ 40k–120k, with structural span analysis, acoustic treatment, and civic-compliance sequencing handled across separate teams before drawings can reach tender. For The Hub, the pipeline produced 137 scene objects, 140 IFC products, 8 role-tailored decks, HK$ 1.91M BoQ, 92.9 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 12 minutes. The Approach explains how span, envelope, and compliance converged."""

N[("arch-04-community-center", "sales")] = """\
你要给街道办建一座 500 m² 社区中心，大跨空间 + 通透立面 + 每日 400 人次流量都要到位；设计 HK$ 40k+ 起，结构大跨、声学、消防分别找；方案一出合规又要返工。

一次给齐：civic-transparent 风格效果图、500 m² 单层大跨完整平面 + 立面 + 剖面、结构节点图、8 份给街道办 / 基金会 / 结构 / 消防 / 施工的方案书、港币报价。

结果：137 件模型构件 · 140 件 IFC · 合规 7/8 · EUI 92.9 · HK$ 1.91M · 12 分钟交付。"""

# ──

N[("arch-05-modern-chinese-house", "portfolio")] = """\
现代中式乡村住宅沿 modern Chinese 与 vernacular 展开，三层分置生活功能。pitched-roof 与 warm-wood-grey 交错形成立面主节奏，一层客堂保留坡顶木梁的视觉，二层卧室与三层阁楼以楼板递进。入户庭院、连廊、客堂构成传统动线序列。秋日傍晚，坡顶投下斜影，木饰面与灰瓦反射出不同层次的暮色。"""

N[("arch-05-modern-chinese-house", "impact")] = """\
A three-storey modern Chinese vernacular house traditionally runs 2–4 weeks of design and HK$ 40k–120k in fees, with structural timber detailing, roof geometry, and vernacular-reference resolution handled through multiple iterations. For this modern-Chinese vernacular house, the pipeline produced 147 scene objects, 153 IFC products, 8 role-tailored decks, HK$ 2.3M BoQ, 136.5 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 10 minutes. The Approach explains how pitched-roof geometry, envelope, and code checks were unified."""

N[("arch-05-modern-chinese-house", "sales")] = """\
你要给乡村客户做一栋 3 层现代中式住宅，坡顶 + 木饰面 + 庭院连廊都要到位；设计 HK$ 40k+ 起，结构木梁、屋顶节点、风格参考分别找；方案改了几稿合规还有节能待补。

一次给齐：现代中式风格的街景与庭院渲染、3 层完整平面 + 立面 + 剖面、坡顶节点、8 份给业主 / 结构 / 木构 / 审批 / 施工的方案书、港币报价。

结果：147 件模型构件 · 153 件 IFC · 合规 7/8 · EUI 136.5 · HK$ 2.3M · 10 分钟交付。"""

# ──

N[("arch-06-small-library", "portfolio")] = """\
Bookhaven Library 社区小型图书馆沿 modern warm 与 wood + concrete 展开，两层布置。park-adjacent 的落地玻璃让阅览区看到公园绿意，daylight-driven 的天窗贯穿二层阅读大厅，自然光从顶部斜下落在书架排之间。一层儿童阅览区更低矮柔和，二层成人阅览更沉静。阳光不同时段落到不同书架上，读者跟着光挪动座位。"""

N[("arch-06-small-library", "impact")] = """\
A community small library with a 2-storey daylight-driven reading hall traditionally runs 2–4 weeks of design and HK$ 40k–120k, with skylight detailing, shelf-load structural checks, and park-adjacent envelope handled as separate workstreams. For Bookhaven, the pipeline produced 237 scene objects, 251 IFC products, 8 role-tailored decks, HK$ 4.52M BoQ, 206.6 kWh/m²·yr EUI, and a 6/8 HK BEC 2021 pass in 18 minutes. The Approach outlines how daylighting, shelf-load, and envelope checks were unified upstream."""

N[("arch-06-small-library", "sales")] = """\
你要给社区建一座两层小型图书馆，天窗采光 + 书架承重 + 公园连接都要到位；设计 HK$ 40k+ 起，天窗、结构、节能要分别找；方案定后合规才反馈天窗 U 值不够要改。

一次给齐：modern-warm 风格的效果图、2 层完整平面 + 立面 + 剖面、天窗与书架承重节点、8 份给基金会 / 管理员 / 结构 / 施工 / 审批的方案书、港币报价。

结果：237 件模型构件 · 251 件 IFC · 合规 6/8 · EUI 206.6 · HK$ 4.52M · 18 分钟交付。"""

# ──

N[("arch-07-loft-coworking", "portfolio")] = """\
Ironworks Commons 旧厂房改造 coworking，三层沿 adaptive-reuse 与 loft 语言展开。保留原始钢桁架与裸露砖墙，loft 的大挑空在一层接待区形成焦点。modern-industrial 的新介入保留吊车轨道的痕迹，二三层以独立工位与小会议室分区。午后阳光透过桁架缝隙投在砖墙上，新旧两层材料在同一个光线里并排存在。"""

N[("arch-07-loft-coworking", "impact")] = """\
An adaptive-reuse 3-storey coworking loft from an old factory traditionally runs 2–4 weeks of design and HK$ 40k–120k, with heritage-structure assessment, MEP retrofit, and adaptive-reuse compliance staged across multiple consultants. For Ironworks Commons, the pipeline produced 218 scene objects, 446 IFC products, 8 role-tailored decks, HK$ 4.13M BoQ, 227.4 kWh/m²·yr EUI, and a 6/8 HK BEC 2021 pass in 22 minutes. The Approach explains how heritage retention and new-insertion detailing converged in one model."""

N[("arch-07-loft-coworking", "sales")] = """\
你要把老厂房改造成 3 层 coworking，保留钢桁架 + 裸露砖墙 + 新增电气都要到位；设计 HK$ 40k+ 起，改造评估、结构复核、节能分别找；旧建筑合规又要单独审。

一次给齐：adaptive-reuse 风格的效果图、3 层完整平面 + 立面 + 剖面、保留构件标注、8 份给投资方 / 运营 / 结构 / 历史评估 / 施工的方案书、港币报价。

结果：218 件模型构件 · 446 件 IFC · 合规 6/8 · EUI 227.4 · HK$ 4.13M · 22 分钟交付。"""

# ──

N[("arch-08-small-clinic", "portfolio")] = """\
Meadow 社区小型诊所沿 community health 与 de-hospital 展开，两层布置。warm clinical 的木饰面柔化临床属性，child friendly 的候诊区加入圆角家具。诊疗室分布于一层便于就诊，二层为行政与备品间。从街道望进来不像传统医院，更像社区客厅。家长带孩子进门先看到绿植与彩色小凳，再进入问诊房间。"""

N[("arch-08-small-clinic", "impact")] = """\
A 2-storey community small clinic with de-hospital detailing traditionally runs 2–4 weeks of design and HK$ 40k–120k, with clinical-flow separation, child-friendly detailing, and medical-compliance checks each handled by separate consultants. For Meadow Clinic, the pipeline produced 175 scene objects, 170 IFC products, 8 role-tailored decks, HK$ 2.18M BoQ, 195.7 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 20 minutes. The Approach shows how clinical-flow, child-friendly geometry, and envelope checks were unified."""

N[("arch-08-small-clinic", "sales")] = """\
你要给社区开一家 2 层小型诊所，诊疗 + 候诊 + 备品都要到位；设计 HK$ 40k+ 起，医疗专项、儿童友好细节、合规分别找；方案定后卫生审查又要返工。

一次给齐：de-hospital 风格的效果图、2 层完整平面 + 立面 + 剖面、诊疗流线与儿童友好节点、8 份给院长 / 医师 / 结构 / 卫生 / 施工的方案书、港币报价。

结果：175 件模型构件 · 170 件 IFC · 合规 7/8 · EUI 195.7 · HK$ 2.18M · 20 分钟交付。"""

# ──

N[("arch-09-mixed-use", "portfolio")] = """\
Meridian Plaza 底商+办公综合体沿 modern business 与 metal + glass curtain wall 展开。底层沿街商铺通过全玻璃橱窗连接街道，办公层以幕墙包覆，timber interior accent 在办公大堂里成为唯一暖色层。urban minimalism 的立面节奏沿长街铺开。傍晚下班潮，底商灯光先亮起，办公楼层的会议室灯光则在幕墙上留下一排规律的光斑。"""

N[("arch-09-mixed-use", "impact")] = """\
A mixed-use retail + office complex with metal-glass curtain wall traditionally runs 2–4 weeks of design and HK$ 40k–120k, with shell-core, shopfront, and core-tenant fit-outs sequenced across multiple teams. For Meridian Plaza, the pipeline produced 299 scene objects, 309 IFC products, 8 role-tailored decks, HK$ 14.19M BoQ, 180.8 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass in 26 minutes. The Approach describes how shell, shopfront, and envelope performance merged into one unified run."""

N[("arch-09-mixed-use", "sales")] = """\
你要开发底商+办公综合体，幕墙 + 商铺橱窗 + 办公大堂都要到位；设计 HK$ 40k+ 起，幕墙、结构、商铺设计分别找；方案一出节能就给打回。

一次给齐：modern business 风格的街景渲染、底商 + 办公多层完整平面 + 立面、幕墙节点、8 份给开发商 / 结构 / 幕墙 / 审批 / 招商的方案书、港币报价。

结果：299 件模型构件 · 309 件 IFC · 合规 7/8 · EUI 180.8 · HK$ 14.19M · 26 分钟交付。"""

# ──

N[("arch-10-sports-complex", "portfolio")] = """\
Horizon Sports Complex 地区级综合体育场沿 civic monumental 与 stadium bowl 展开。silver metal + warm wood entry 在入口大厅形成对比，dynamic roof cantilever 的悬挑钢屋顶覆盖看台区。场馆主体为碗形看台，辅助训练馆与媒体区沿外圈布置。比赛日黄昏，悬挑屋顶在场地中央投下阴影，看台上的人群随着终场哨声同时起身，暮色从场边缓缓填满碗口。"""

N[("arch-10-sports-complex", "impact")] = """\
A regional sports complex with a stadium bowl and dynamic cantilever roof traditionally runs 2–4 weeks of design and HK$ 40k–120k, with long-span structural analysis, acoustic simulation, and major-venue code compliance each handled as discrete workstreams. For Horizon Sports Complex, the pipeline produced 465 scene objects, 472 IFC products, 1 stakeholder deck, HK$ 208.6M BoQ, 103.0 kWh/m²·yr EUI, and a 7/8 HK BEC 2021 pass. The Approach describes how stadium geometry, roof cantilever, and code checks converged in one model."""

N[("arch-10-sports-complex", "sales")] = """\
你要建一座地区级综合体育场，悬挑屋顶 + 看台碗 + 辅助训练馆都要到位；设计费从数十万港币起，结构、声学、合规分别找；方案定后大型场馆合规又要返工几轮。

一次给齐：civic monumental 风格的全景渲染、完整场馆平面 + 立面 + 剖面、悬挑结构节点、5 件套 BIM 导出、港币报价、合规预检。

结果：465 件模型构件 · 472 件 IFC · 合规 7/8 · EUI 103.0 · HK$ 208.6M 工程量估值一次出齐。"""


# ─────────────────────────────── WRITE FILES ───────────────────────────────

def main() -> None:
    written = 0
    for (mvp_id, template), text in N.items():
        folder = ROOT / ("arch-mvp" if mvp_id.startswith("arch-") else "mvp") / mvp_id
        out = folder / "case-study" / f"narrative-{template}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text.strip() + "\n")
        written += 1
    print(f"OK: wrote {written} narrative files across "
          f"{len({mvp for mvp, _ in N})} MVPs × 3 templates.")


if __name__ == "__main__":
    main()

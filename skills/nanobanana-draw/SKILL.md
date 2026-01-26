---
name: nanobanana-draw
description: 使用 Nanobanana (Gemini 3 Pro Image) 生成图片,支持中英文描述自然语言画图。
allowed-tools: Bash(python:*), Read, Write, WebSearch
---

# Nanobanana 画图工具

通过 OpenRouter API 调用 Nanobanana (Google Gemini 3 Pro Image) 模型生成图片。

## 快速开始

### 环境配置

设置 OpenRouter API key：

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

或创建 `.env` 文件（放在 skill 根目录）：

```bash
OPENROUTER_API_KEY=sk-or-...
NANOBANANA_MODEL=google/gemini-3-pro-image-preview
OPENROUTER_SITE_URL=https://your-site.example
OPENROUTER_APP_NAME=nanobanana-draw
```

### 基础使用

```bash
cd .claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "画一只可爱的橘猫,坐在阳光下"
```

### 从标准输入读取

```bash
echo "画一幅赛博朋克风格的城市夜景" | python scripts/nanobanana_draw.py
```

### 添加系统提示词

```bash
python scripts/nanobanana_draw.py \
  --system "你是专业的插画师,擅长创作细节丰富的插画" \
  "画一只在森林里探险的小狐狸"
```

## 工作流（必须遵循）

收到 ARGUMENTS 后，**必须按顺序执行以下步骤**，不可跳过：

⚠️ **ARGUMENTS 是用户的原始需求输入，不是最终 prompt，禁止直接传给脚本。**

### Step 1: 理解画图需求

与用户确认:
- 画面主题和内容
- 风格偏好(写实/卡通/赛博朋克/水彩等)
- 特殊要求(色调/构图/细节等)

### Step 2: 搜索参考图（重要实体）⚠️ 必须执行

**对于专有名词、品牌、产品、图标等具体实体，必须先搜索参考，不可跳过：**

识别 prompt 中的以下类型词汇：
- 品牌/产品名：豆包、Claude、ChatGPT、微信、抖音等
- 图标/Logo：App 图标、公司 Logo、软件界面等
- 具体人物：名人、角色、IP 形象等
- 特定建筑/地标：东方明珠、故宫、埃菲尔铁塔等
- 专业术语：特定的设计风格、艺术流派等

**搜索方法：**

使用 WebSearch 搜索参考图：
```
WebSearch: "豆包 App 图标"
WebSearch: "Claude AI logo"
WebSearch: "赛博朋克 城市 参考图"
```

将搜索到的视觉特征融入 prompt：
- 颜色：主色调、配色方案
- 形状：轮廓、结构特征
- 风格：设计语言、视觉风格

**示例：**

用户说："画一个豆包的图标"

1. 先搜索：`WebSearch: "豆包 App 图标 设计"`
2. 了解到：豆包图标是蓝紫色渐变背景，中间有白色气泡对话框图案
3. 组织 prompt："画一个 App 图标，蓝紫色渐变背景，中间是白色的气泡对话框图案，圆角矩形，现代简约风格"

---

### Step 2.5: 人物肖像类 ⚠️ 特殊流程（必须执行）

**当用户要求画「肖像」时，默认使用以下固定风格，无需询问：**

**默认风格：简约线刻 + 彩色衣服**
- 背景极简：纯白色或浅米色，干净留白
- 人物面部：黑白线条刻画，木刻版画质感
- 衣服：保留鲜艳彩色，作为视觉焦点
- 效果：黑白 + 彩色对比，吸引眼球

#### 2.5.1 使用 firecrawl 搜索人物照片

```python
mcp__firecrawl__firecrawl_search(
    query="人物名 照片",
    sources=[{"type": "images"}],
    limit=5
)
```

#### 2.5.2 下载照片到本地

```bash
curl -s -o /tmp/person_photo.jpg "照片URL"
```

#### 2.5.3 使用默认 Prompt 生成（直接复制使用）

```bash
python scripts/nanobanana_draw.py "将这张照片中的人物转换为黑白线刻版画风格，但衣服保留彩色：
- 人物面部用精细的黑白平行线条刻画，木刻版画质感
- 衣服保留鲜艳的彩色（根据照片中的衣服颜色），形成视觉焦点
- 背景极简：纯白色或浅米色，干净留白
- 黑白线条人像 + 彩色衣服的对比，吸引眼球
- 整体风格：简约现代的线刻插画" --image /tmp/person_photo.jpg --style "线刻肖像" --subject "人物名"
```

#### 完整示例：生成贾国龙肖像

```bash
# Step 1: 搜索真实照片
mcp__firecrawl__firecrawl_search(
    query="贾国龙 西贝 创始人 照片",
    sources=[{"type": "images"}],
    limit=5
)

# Step 2: 下载照片
curl -s -o /tmp/jia_guolong.jpg "照片URL"

# Step 3: 用默认 prompt 生成
python scripts/nanobanana_draw.py "将这张照片中的人物转换为黑白线刻版画风格，但衣服保留彩色：
- 人物面部用精细的黑白平行线条刻画，木刻版画质感
- 衣服保留鲜艳的彩色（深蓝色polo衫），形成视觉焦点
- 背景极简：纯白色或浅米色，干净留白
- 黑白线条人像 + 彩色衣服的对比，吸引眼球
- 整体风格：简约现代的线刻插画" --image /tmp/jia_guolong.jpg --style "线刻肖像" --subject "贾国龙肖像"
```

#### 注意事项

1. **默认风格**：用户说「肖像」就用上面的 prompt，不要问风格
2. **照片选择**：优先选择正面、清晰、光线好的照片
3. **衣服颜色**：根据照片实际衣服颜色调整 prompt 中的颜色描述
4. **参考图用法**：`--image` 参数传入本地照片路径

---

### Step 3: 组织 Prompt

基于用户需求和参考搜索结果构建详细的画图 prompt:
- 主体描述清晰
- 风格明确
- 氛围和细节丰富
- 使用中文或英文均可
- **融入搜索到的具体视觉特征**

### Step 3.5: 确定风格和主题（文件命名用）

调用脚本前，从用户需求中提取：

**风格（--style）**：必须从以下预定义列表中选择，不匹配则用"其他"：
- `手绘白板` / `对比漫画` / `学霸笔记` / `杂志大字` / `荧光划线`
- `科技渐变` / `撕纸拼贴` / `神秘贴纸` / `人物语录` / `线刻肖像`
- `其他`（不属于以上任何一种时使用）

**主题（--subject）**：用 2-8 个中文字概括画面核心内容。
示例：`AI学习路径`、`橘猫晒太阳`、`贾国龙肖像`、`城市夜景`

### Step 4: 调用脚本

```bash
cd .claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "你的画图描述" --style "风格名" --subject "主题"
```

生成文件命名格式：`{YYYYMMDD}_{风格}_{主题}_{序号}.{扩展名}`
示例：`20260124_手绘白板_AI学习路径_0.png`

### Step 5: 返回结果

输出 Nanobanana 生成的图片描述或链接,并根据用户反馈进行调整。

## 输出格式

- 默认:仅输出模型回复(图片链接或描述)
- `--print-json`:输出完整 JSON
- `--output result.json`:保存完整响应到文件

## 依赖安装

```bash
cd .claude/skills/nanobanana-draw
pip install -r scripts/requirements.txt
```

## 在 Claude Code 中使用

在 Claude Code 中直接说:

```
画一只可爱的柴犬
画一幅赛博朋克风格的城市
帮我画一张产品设计图
```

Claude 会自动调用该 skill 为你生成图片。

## 常见提示词模板

### 角色/人物
```
画一个可爱的动漫女孩,长发飘逸,穿着校服,在樱花树下微笑
```

### 场景/风景
```
画一幅日落时分的海边,温暖的橘色天空倒映在平静的海面上
```

### 概念/设计
```
画一个未来科技感的智能手表界面设计,简约现代风格
```

### 抽象/艺术
```
画一幅抽象派风格的作品,用蓝色和金色表达宁静与希望的主题
```

## 平台最佳尺寸

### 小红书

| 类型 | 比例 | 推荐像素 | 说明 |
|------|------|----------|------|
| **图文笔记（推荐）** | 3:4 竖版 | 1080×1440px | 首选，展示效果最佳 |
| 正方形 | 1:1 | 1080×1080px | 通用 |
| 横版 | 4:3 | 1440×1080px | 风景/横幅 |

生成小红书图片时，在 prompt 中指定尺寸：
```
画一张小红书封面图，3:4竖版比例，1080x1440像素，主题是...
```

### 其他平台参考

| 平台 | 推荐比例 | 像素 |
|------|----------|------|
| 微信公众号封面 | 2.35:1 | 900×383px |
| 朋友圈配图 | 1:1 | 1080×1080px |
| 抖音封面 | 9:16 | 1080×1920px |

## 技术细节

- 默认模型: `google/gemini-3-pro-image-preview`
- 支持通过 `--model` 参数切换模型
- Temperature 默认 0.7,可通过 `--temperature` 调整
- 支持 `--max-tokens` 限制输出长度

## 故障排查

如果遇到问题:
1. 确认 OPENROUTER_API_KEY 已正确设置
2. 检查网络连接
3. 确认 API key 有效且有足够额度
4. 查看错误信息中的详细提示

---

## 小红书封面设计模式

本节收集了小红书高传播内容的封面设计模式，可直接套用。

### 设计模式速查表

| 设计模式 | 适用场景 | 效果 |
|----------|----------|------|
| **手绘白板风格** ⭐ | 流程图、知识框架、方法论、AI/科技话题 | **优先推荐**，高级感+专业感 |
| **上下对比漫画风格** ⭐ | 对比、反差、吐槽、生活感悟 | 可爱有趣，传播性强 |
| **学霸笔记风格** ⭐ | 知识图解、原理拆解、对比科普、烹饪/健身/科学 | 高信息密度，教科书质感 |
| 杂志大字风格 | 观点金句、核心论点、简短有力 | 极致简约，高端感 |
| 荧光笔划线风格 | 干货教程、步骤方法、学习笔记 | 学习笔记感 |
| 科技渐变风格 | 赛博朋克、AI、编程、未来科技 | 科技感、未来感 |
| 撕纸拼贴风格 | 生活感悟、旅行日记、情感类 | 文艺、治愈 |
| **神秘人物贴纸风格** | 个人IP头像、NFT风格、潮流账号、匿名形象 | 潮酷神秘、辨识度高 |
| **人物语录风格** ⭐ | 名人金句、书摘语录、知识IP内容 | 高级感+文化感，适合批量出图 |

---


### 模式 0：手绘白板风格 ⭐ 优先推荐

**适用场景：** 流程图、知识框架、方法论、系统架构、AI/科技话题、商业概念可视化

**设计特点：**
- 类似 Excalidraw 的手绘草图美学
- 极简线条艺术，粗黑马克笔线条
- 蓝色高亮点缀作为强调色
- 简单涂鸦图标 + 流程图结构
- 纯白背景，干净专业
- 箭头连接各元素，展示数据流/逻辑流

**Prompt 模板：**

```
生成一张小红书风格封面图，3:4竖版比例，
手绘白板草图风格，视觉笔记美学，
极简线条艺术，粗黑马克笔线条，蓝色高亮点缀，
简单涂鸦图标，流程图结构，箭头连接各元素，
纯白背景，干净专业，商业概念可视化。

顶部标题：「[主标题]」用粗体手写风格，蓝色下划线强调。

内容布局（从左到右/从上到下的流程）：
- 第一部分「[模块名]」：[图标描述1]、[图标描述2]
- 第二部分「[模块名]」：[图标描述1]、[图标描述2]
- 第三部分「[模块名]」：[图标描述1]、[图标描述2]

用粗箭头连接各部分，展示流程走向。
风格：Excalidraw 手绘美学，无阴影，无渐变，无3D效果，略带不规则的草图线条。
```
**常用图标关键词：**

| 类别 | 图标描述（英文） |
|------|------------------|
| 科技 | robot head, chip, neural network, code symbols, AI brain |
| 数据 | database, folder, cloud storage, magnifying glass |
| 社交 | smartphone, chat bubble, user avatar, globe |
| 工具 | gear, wrench, lightning bolt, rocket |
| 知识 | book, lightbulb, brain, graduation cap |
| 商业 | chart, coin, handshake, trophy, dollar sign |

**示例 Prompt：**

```
Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art,
bold black marker strokes with blue highlight accents,
pure white background, clean and professional.

Title: 「AI Learning Path」in bold hand-drawn style with blue underline.

Layout (top to bottom):
- Foundation: book icon「Theory」, code icon「Programming」
- Core: brain icon「Model Principles」, gear icon「Engineering」
- Application: rocket icon「Projects」, trophy icon「Iteration」

Arrows flowing downward, Excalidraw hand-drawn aesthetic.
```

---

### 模式 0.5：上下对比漫画风格 ⭐ 推荐

**适用场景：** 对比、反差、吐槽、生活感悟、"上不...下不..."句式、理想vs现实

**设计特点：**
- 纯白背景，上下分为两个独立画框
- **大量留白**：画框内空间要大，元素不拥挤，角色居中且周围留白充足
- 画框边框：圆角波浪形边框（柔和感）或细黑色边框，颜色可用绿色/黑色
- **上下画框间距明显**：两个框之间要有足够的白色间隔
- 画框内部有粗体黑色标题文字（底部或顶部）
- 同一个可爱卡通角色（兔子、猫咪、小人等）出现在两个场景
- 角色表情一致但手持/面对不同物品，形成反差
- 简约线条，柔和配色（米黄、浅粉、浅绿点缀）
- 形成"上...下..."的对比叙事
- **整体干净清爽，宁少勿多**

**Prompt 模板：**

```
Xiaohongshu style comic, 3:4 vertical ratio (1080x1440px),
pure white background, divided into TWO panels stacked vertically,
LOTS OF WHITE SPACE between and around panels.

Each panel has rounded wavy border (soft green or black color),
GENEROUS PADDING inside each panel - elements should not feel crowded.

TOP PANEL:
- Bold black title text at bottom of panel:「[上半句]」
- Cute kawaii [角色] character CENTERED with plenty of space around
- Character holding/facing [物品A]
- Clean minimal style, soft colors, breathable layout

BOTTOM PANEL:
- Bold black title text at bottom of panel:「[下半句]」
- Same cute [角色] character CENTERED
- Character holding/facing [物品B] (contrasting with panel 1)
- Same art style as top panel

Style: Japanese kawaii illustration, simple line art,
pastel accents (light yellow body, pink cheeks),
minimalist comic panel layout, cute and humorous contrast.
KEY: Maximum white space, clean and airy feel, less is more.
```

**示例 Prompt：**

```
Xiaohongshu style comic, 3:4 vertical ratio,
pure white background, two panels stacked vertically,
LOTS OF WHITE SPACE, panels have rounded wavy green borders.

TOP PANEL:
- Cute kawaii bunny character CENTERED with generous space around
- Bunny holding a Chanel handbag, looking confused
- Bold black text at bottom:「上不认识奢侈品」
- Clean minimal style, airy layout

BOTTOM PANEL:
- Same cute bunny character CENTERED
- Bunny holding a Chinese cabbage/lettuce, same confused expression
- Bold black text at bottom:「下不认识地里的菜」
- Same art style, plenty of breathing room

Style: Japanese kawaii, simple line art, soft pastel colors,
cute comic panel format, humorous self-deprecating vibe.
KEY: Maximum white space, less is more, clean and refreshing.
```

**常用对比句式：**

| 上半句 | 下半句 | 主题 |
|--------|--------|------|
| 上不认识奢侈品 | 下不认识地里的菜 | 自嘲/生活 |
| 理想中的我 | 现实中的我 | 反差萌 |
| 上班前 | 下班后 | 职场吐槽 |
| 计划中 | 实际上 | 拖延症 |
| 别人眼中的我 | 真实的我 | 人设反差 |

---

### 模式 0.8：学霸笔记风格 ⭐ 推荐

**适用场景：** 知识图解、原理拆解、对比科普（错误vs正确做法）、烹饪/健身/科学/工程类干货、步骤流程图解

**设计特点：**
- 浅蓝色方格纸背景（graph paper），学生笔记本质感
- 顶部超大粗体手写标题（黑色，居中）
- ❌/✅ 对比分区：上半"错误做法"（红色标记），下半"正确做法"（绿色标记）
- 写实水彩手绘插图（物品、器具、食材等），细节丰富
- 密集标注系统：
  - 红色/橙色箭头指向关键部位
  - 花括号 `{` 分层标注（如成分分层）
  - 中英双语术语标注
  - 温度计、火焰、警告等小图标
- 步骤流程用粗箭头 → 连接
- 高信息密度，像教科书插图
- 水平分割线隔开不同区域

**Prompt 模板：**

```
Xiaohongshu educational infographic, 3:4 vertical ratio (1080x1440px),
light blue graph paper background (faint grid lines),
study notes / textbook illustration aesthetic.

TOP: Bold hand-drawn title centered:「[主标题]」
black brush font, largest size.

SECTION 1 (upper half) - WRONG WAY ❌:
- Red ❌ icon + subtitle:「[错误做法标题]」in red bold text
- Realistic watercolor illustration of [具体场景/物品]
- Annotation arrows (red/orange) pointing to key parts:
  - Curly brace { labeling layers: [层1], [层2], [层3]
  - Temperature/warning icons with values
  - Bilingual labels: [中文] ([English])
- Small warning icon/gauge showing danger threshold

--- horizontal divider line ---

SECTION 2 (lower half) - RIGHT WAY ✅:
- Green ✅ icon + subtitle:「[正确做法标题]」in green bold text
- Step-by-step flow with thick arrows →:
  - Step 1 「[步骤名]」: [图标+描述]
  - Step 2 「[步骤名]」: [图标+描述]
  - Step 3 「[步骤名]」: [图标+描述]
- Realistic watercolor illustration showing correct result
- Green checkmark annotations for key points

Style: Dense educational infographic, realistic watercolor objects,
hand-drawn annotation arrows, bilingual labels,
textbook diagram quality, high information density.
Color: red for warnings, green for correct, black for text,
warm tones for illustrations, light blue grid background.
```

**示例 Prompt（烹饪类）：**

```
Xiaohongshu educational infographic, 3:4 vertical ratio,
light blue graph paper background with faint grid lines,
study notes aesthetic, dense informative layout.

TOP: Bold hand-drawn title:「别直接下黄油！」black brush font.

UPPER SECTION ❌「黄油的150°C陷阱 (The Burn Trap)」:
- Realistic watercolor cross-section of a frying pan
- Curly brace labeling butter layers: 水份(Water), 中间脂肪(Yellow Fat), 底层固体(White Solids)
- Red arrows showing smoke rising, label: 烟点(Smoke Point)≈150°C
- Small fire icon with text: 蛋白质焦化(苦味来源)
- Temperature gauge warning icon: 150°C WARNING

--- divider ---

LOWER SECTION ✅「正确姿势：Butter Basting（后期淋洗）」:
- Flow: 煎制全程(高温植物油) → 最后1分钟(关火/移锅) → 仅萃取香气
- Thermometer icons: 高温 High Heat (>200°C) → OFF → 130°C
- Realistic watercolor: steak in pan being basted with butter
- Green checkmark: 出锅前淋洗

Style: textbook infographic, watercolor realism, dense annotations,
bilingual labels, educational diagram aesthetic.
```

**标注系统关键词：**

| 标注类型 | Prompt 描述 |
|----------|------------|
| 箭头标注 | red/orange annotation arrows pointing to [部位] |
| 花括号分层 | curly brace { labeling layers |
| 温度/数值 | temperature gauge/thermometer icon showing [值] |
| 警告图标 | warning icon, fire icon, danger symbol |
| 步骤流程 | thick arrows → connecting steps |
| 中英标注 | bilingual label: 中文 (English) |
| 对勾/叉号 | green ✅ checkmark / red ❌ cross |

**适配主题举例：**

| 主题 | 错误做法 | 正确做法 |
|------|----------|----------|
| 烹饪 | 直接大火炒 | 分步控温 |
| 健身 | 错误发力姿势 | 正确肌肉激活 |
| 护肤 | 叠加太多产品 | 精简有效步骤 |
| 编程 | 直接写代码 | 先设计后编码 |
| 咖啡 | 沸水直接冲 | 控温分段萃取 |

---

### 模式 1：杂志大字风格

**适用场景：** 观点输出、金句分享、高端内容

**设计特点：**
- 纯白背景，极致留白
- 1-2 个超大号关键词
- 纯黑文字，黑白强对比
- 无任何装饰元素

**Prompt 模板：**

```
Xiaohongshu cover image, 3:4 vertical ratio,
pure white background (#FFFFFF), no texture,
only 1-2 oversized keywords as main title: 「[核心关键词]」,
Helvetica or Song Ti font style,
pure black text (#000000), extreme black and white contrast,
lots of white space, no decorative elements,
magazine editorial minimalist style.
```

**示例：**
```
Xiaohongshu cover image, 3:4 vertical ratio,
pure white background, no texture,
oversized keyword: 「离钱近的代码」,
pure black bold text, extreme contrast,
massive white space, no decoration, magazine style.
```

---

### 模式 2：荧光笔划线风格

**适用场景：** 知识干货、学习笔记、经验总结

**设计特点：**
- 米白色笔记本内页
- 带淡灰色横线纹理
- 黄色荧光笔高亮关键词
- 多层级字号
- 角落"干货分享"标注

**Prompt 模板：**

```
Xiaohongshu cover image, 3:4 vertical ratio,
Muji style cream/beige notebook page with faint gray horizontal lines,
main title in bold dark gray font with multiple font sizes,
keywords「[关键词1]」「[关键词2]」highlighted with yellow highlighter effect,
corner annotation saying "干货分享" or "建议收藏" in small text,
clean study notes aesthetic, warm and inviting.
```

---

### 模式 3：科技渐变风格

**适用场景：** 赛博朋克、AI、编程、未来科技

**设计特点：**
- 深蓝到紫色渐变背景
- 白色或霓虹蓝文字
- 发光粒子效果
- 未来感、科技感

**Prompt 模板：**

```
Xiaohongshu cover image, 3:4 vertical ratio,
deep blue to purple gradient background,
center white bold title: 「[主标题]」,
subtitle in neon blue glow: 「[副标题]」,
floating glowing particles, futuristic tech aesthetic,
minimalist cyberpunk style, centered layout.
```

---

### 模式 4：撕纸拼贴风格

**适用场景：** 生活感悟、旅行日记、情感类

**设计特点：**
- 纯白背景 + 撕边纸片
- 细微自然阴影，立体拼贴感
- 手写体标题
- 和纸胶带装饰

**Prompt 模板：**

```
Xiaohongshu cover image, 3:4 vertical ratio,
pure white background with a torn-edge white paper piece placed on it,
paper has subtle natural shadow creating collage depth effect,
title in handwritten black font, centered,
top-left corner has a semi-transparent washi tape sticker (diagonal stripes or polka dots),
add a simple line drawing icon related to the content,
minimalist artistic journaling style.
```

---

### 模式 5：神秘人物贴纸风格

**适用场景：** 个人IP头像、NFT风格头像、潮流账号形象、匿名博主人设、街头潮牌内容

**设计特点：**
- 极简矢量插画风格（Flat Vector Illustration）
- 深色纹理背景（黑色/深灰带噪点）
- 贴纸艺术效果：粗白色描边轮廓
- 神秘匿名人物：无面部特征，用墨镜/口罩/帽子遮挡
- 高饱和度单色系服装（红、紫、蓝等）
- 居中半身像构图
- 街头潮流/Urban 美学

**Prompt 模板：**

```
A minimalist vector illustration of a mysterious anonymous figure,
wearing a [颜色] oversized hoodie with hood up,
[配饰描述：口罩/墨镜/耳机等],
[特殊元素：发光眼睛/手持物品等],
no visible face, anonymous character,
dark textured background with subtle noise texture,
flat design style, sticker art with thick white outline border,
urban streetwear aesthetic, [风格：cyberpunk/street style/NFT avatar],
centered composition, high contrast colors, clean sharp edges.
```

**可替换元素：**

| 元素 | 选项示例 |
|------|----------|
| 服装颜色 | bright red, deep purple, electric blue, neon green, black |
| 配饰 | white medical mask, black sunglasses, large headphones over hood, baseball cap |
| 特殊元素 | neon glowing eyes, holding coffee cup, phone gesture, crossed arms |
| 风格氛围 | cyberpunk vibe, street style, NFT avatar style, anime influence |

**示例 Prompt 1（红色街头风）：**

```
A minimalist vector illustration of a mysterious anonymous figure,
wearing a bright red oversized hoodie with "STREETWEAR" text,
white medical mask, black sunglasses, hood up covering most of face,
one hand raised near head in phone gesture,
dark textured background with subtle noise,
flat design style, sticker art with thick white outline border,
urban streetwear aesthetic, NFT avatar style,
centered composition, high contrast colors.
```

**示例 Prompt 2（紫色赛博朋克风）：**

```
A minimalist vector illustration of a mysterious anonymous figure,
wearing a deep purple oversized hoodie,
large black headphones over the hood,
neon green glowing eyes visible in shadow under hood, no face visible,
holding a white coffee cup with steam rising,
dark textured background with subtle noise texture,
flat design style, sticker art with thick white outline border,
urban streetwear aesthetic, cyberpunk vibe, NFT avatar style,
centered composition, high contrast colors, clean sharp edges.
```

**配色建议：**

| 风格 | 服装色 | 背景 | 点缀色 |
|------|--------|------|--------|
| 经典街头 | 红色 #E53935 | 黑色 #1A1A1A | 白色描边 |
| 赛博朋克 | 紫色 #7C3AED | 深灰 #1F1F1F | 霓虹绿 #39FF14 |
| 暗黑极简 | 黑色 #000000 | 深灰 #2D2D2D | 白色/灰色 |
| 活力潮流 | 蓝色 #2563EB | 黑色 #0F0F0F | 橙色 #F97316 |

---

### 模式 6：人物语录风格 ⭐ 推荐

**适用场景：** 名人金句、书摘语录、知识IP内容、读书笔记分享、文化类账号

**设计特点：**
- 分两步生成：AI生成木刻肖像 + Python脚本合成语录卡片
- 人物：高对比度黑白木刻/铜版画风格（crosshatching 交叉排线）
- 背景：纯色平涂（默认钴蓝 #0047AB，可换色）
- 文字浮层：白色半透明圆角卡片 + 粗体语录 + 署名
- 整体效果：严肃知识分子气质，文化感强

**完整流程：**

#### Step 1: 搜索人物照片

```python
mcp__firecrawl__firecrawl_search(
    query="人物名 照片",
    sources=[{"type": "images"}],
    limit=5
)
```

#### Step 2: 下载照片

```bash
curl -s -o /tmp/person_photo.jpg "照片URL"
```

#### Step 3: AI 生成木刻肖像

```bash
cd /Users/liuyishou/.claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "将这张照片中的人物转换为高对比度黑白木刻版画风格肖像，放置在纯钴蓝色(cobalt blue)纯色背景上：
- 人物面部和身体完全用精细的黑白交叉排线(crosshatching)刻画，木刻/铜版画质感
- 只有纯黑线条，无灰度过渡，无中间调
- 线条粗犷有力，用排线疏密表现面部明暗和皱纹纹理
- 头发用密集平行线条表现
- 背景是纯粹的钴蓝色(#0047AB)，完全平涂，无任何纹理
- 人物线条与蓝色背景形成强烈对比
- 构图：胸部以上半身像，略微侧面角度
- 整体风格：editorial book cover illustration，严肃知识分子气质
- 类似vintage linocut print的效果
- 不要任何文字" --image /tmp/person_photo.jpg --style "人物语录" --subject "人物名肖像"
```

#### Step 4: 合成语录卡片

```bash
python scripts/quote_portrait.py \
    --portrait [Step3生成的肖像路径] \
    --quote "语录第一行\n语录第二行\n语录第三行" \
    --attribution "—作者名《书名》" \
    --output /tmp/final_output.png
```

**合成脚本参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--portrait` | 肖像图片路径（必填） | - |
| `--quote` | 语录文本，用 `\n` 分行（必填） | - |
| `--attribution` | 署名文字 | 空 |
| `--output` | 输出路径 | 肖像同目录_quote.png |
| `--bg-color` | 背景色（hex） | #0047AB（钴蓝） |
| `--font-size` | 语录字号 | 55 |
| `--attr-font-size` | 署名字号 | 40 |
| `--width` | 输出宽度 | 1080 |
| `--height` | 输出高度 | 1440 |

**背景色推荐：**

| 颜色 | Hex | 适用氛围 |
|------|-----|----------|
| 钴蓝（默认） | #0047AB | 严肃、学术、经典 |
| 深红 | #8B0000 | 激情、力量、革命 |
| 墨绿 | #1B4332 | 沉稳、自然、哲思 |
| 深紫 | #4A0E4E | 神秘、高贵、文艺 |
| 纯黑 | #1A1A1A | 极简、现代、酷 |

**完整示例（刘震云语录）：**

```bash
# 1. 搜索照片
# firecrawl_search query="刘震云 作家 照片" sources=images

# 2. 下载
curl -s -o /tmp/liu_zhenyun.jpg "照片URL"

# 3. 生成木刻肖像
cd /Users/liuyishou/.claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "将这张照片中的人物转换为高对比度黑白木刻版画风格肖像..." --image /tmp/liu_zhenyun.jpg --style "人物语录" --subject "刘震云肖像"

# 4. 合成语录
python scripts/quote_portrait.py \
    --portrait nanobanana_xxx.png \
    --quote "想钱，想女人的男人，\n才是正人君子；\n不敢想，不敢说的男人，\n都是废物。" \
    --attribution "—刘震云《咸的玩笑》" \
    --output /tmp/liu_zhenyun_quote.png
```

---

### 配色方案速查

| 风格 | 背景色 | 字体色 | 适用场景 |
|------|--------|--------|----------|
| 经典极简 | 纯白 #FFFFFF | 黑色 #000000 | 干货、观点、知识 |
| 高级灰 | 浅灰 #F5F5F5 | 深灰 #333333 | 职场、商业、理性 |
| 治愈系 | 奶油黄 #FFF8E7 | 棕色 #5D4037 | 生活、情感、日常 |
| 科技感 | 深蓝 #1A1A2E | 白/霓虹蓝 | AI、编程、科技 |
| 少女感 | 淡粉 #FFE4E6 | 深粉 #DB2777 | 美妆、穿搭、甜系 |

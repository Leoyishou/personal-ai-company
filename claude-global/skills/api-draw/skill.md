---
name: api-draw
description: 综合画图工具 - AI 生图 (Nanobanana/Gemini) + 图片后处理（拼接/抠图/圆形裁剪/合成）。支持中英文自然语言画图。
allowed-tools: Bash(python:*), Read, Write, WebSearch
model: sonnet
tags: [draw, image, nanobanana, gemini]
---

# Draw 画图工具

综合画图工具，包含两大核心能力：
1. **AI 生图**：通过 OpenRouter API 调用 Nanobanana (Google Gemini 3 Pro Image) 模型生成图片
2. **图片处理**：拼接、抠图、圆形裁剪、合成等后处理功能

## 快速开始

```bash
cd ~/.claude/skills/api-draw
python scripts/nanobanana_draw.py "画一只可爱的橘猫,坐在阳光下" --style "其他" --subject "橘猫"
```

环境变量：`OPENROUTER_API_KEY`（存储在 `~/.claude/secrets.env`）

---

## 工作流（必须遵循）

收到 ARGUMENTS 后，**必须按顺序执行以下步骤**，不可跳过：

### Step 1: 理解画图需求

与用户确认画面主题、风格偏好、特殊要求。

**若用户未指定风格，必须用 AskUserQuestion 询问：**

```json
{
  "questions": [{
    "question": "你想要什么风格的图？",
    "header": "图片风格",
    "options": [
      {"label": "手绘白板", "description": "涂鸦风格，适合流程图、架构图、工具推荐"},
      {"label": "板书插画", "description": "教学风格，白板+卡通人物，适合知识科普、教程"},
      {"label": "学霸笔记", "description": "方格纸背景，错误/正确对比，适合干货教学"},
      {"label": "对比漫画", "description": "上下两格漫画，适合反差、吐槽、生活感悟"}
    ],
    "multiSelect": false
  }]
}
```

### Step 2: 搜索参考图（重要实体）

对于品牌/产品名、图标/Logo、具体人物、特定建筑等，必须先 WebSearch 搜索参考，将视觉特征融入 prompt。

### Step 2.5: 人物肖像类特殊流程

用户要求画「肖像」时，直接使用线刻肖像风格，无需询问。流程：
1. firecrawl 搜索人物照片
2. curl 下载到本地
3. 使用 `--image` 参数生成

### Step 3: 加载风格模板

**根据用户选择的风格，读取对应模板文件：**

```
Read("~/.claude/skills/api-draw/templates/[风格名].md")
```

模板包含完整的 Prompt 模板、示例、注意事项。

### Step 4: 组织 Prompt 并调用脚本

```bash
cd ~/.claude/skills/api-draw
python scripts/nanobanana_draw.py "详细的画图描述" --style "风格名" --subject "主题"
```

生成文件命名：`{YYYYMMDD}_{风格}_{主题}_{序号}.{扩展名}`

### Step 5: 返回结果

输出生成的图片，根据用户反馈调整。

---

## 风格模板索引

选定风格后，用 `Read` 工具加载对应模板：

| 风格名 | 模板文件 | 适用场景 |
|--------|----------|----------|
| **手绘白板** | `templates/手绘白板.md` | 流程图、知识框架、方法论、AI/科技话题 |
| **板书插画** | `templates/板书插画.md` | 财经理财、知识科普、教育课程、技术教程 |
| **学霸笔记** | `templates/学霸笔记.md` | 知识图解、原理拆解、错误vs正确对比 |
| **对比漫画** | `templates/对比漫画.md` | 对比、反差、吐槽、生活感悟 |
| **人物语录** | `templates/人物语录.md` | 名人金句、书摘语录、知识IP内容 |
| **人物拼接封面** | `templates/人物拼接封面.md` | UP主介绍、人物专题、创作者故事 |
| **线刻肖像** | `templates/线刻肖像.md` | 人物头像、个人IP形象 |
| 杂志大字 | `templates/杂志大字.md` | 观点金句、核心论点 |
| 荧光划线 | `templates/荧光划线.md` | 知识干货、学习笔记 |
| 科技渐变 | `templates/科技渐变.md` | 赛博朋克、AI、编程 |
| 撕纸拼贴 | `templates/撕纸拼贴.md` | 生活感悟、旅行日记 |
| 神秘贴纸 | `templates/神秘贴纸.md` | 个人IP头像、NFT风格 |

**--style 参数可选值：**
`手绘白板` / `板书插画` / `对比漫画` / `学霸笔记` / `杂志大字` / `荧光划线` / `科技渐变` / `撕纸拼贴` / `神秘贴纸` / `人物语录` / `线刻肖像` / `人物拼接封面` / `其他`

---

## 图片后处理工具

### 图片拼接

**默认设置：水平布局 + 实线框**（用户偏好）

```bash
python scripts/image_stitch.py img1.jpg img2.jpg img3.jpg -o output.jpg -d horizontal --border-style solid
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-d, --direction` | `horizontal`/`h` 或 `vertical`/`v` | **horizontal**（推荐） |
| `-g, --gap` | 图片间距 | 20 |
| `--border-style` | `solid` 或 `dashed` | **solid**（推荐） |

> **注意**：多图合并时，优先使用水平布局+实线框，除非用户明确要求其他方式。

### 抠图

```bash
# 白底抠图（默认）
python scripts/remove_bg.py portrait.jpg -o portrait_nobg.png

# AI智能抠图（需要 pip install rembg）
python scripts/remove_bg.py photo.jpg -o photo_nobg.png --mode ai
```

### 圆形裁剪

```bash
python scripts/circle_crop.py input.png -o output.png --size 300
```

### 图片合成

```bash
python scripts/composite.py --bg main.jpg --fg portrait.png --position top-right -o output.jpg
```

### 人物封面合成（圆框+头像）

```bash
python scripts/portrait_cover.py \
    --bg whiteboard.jpg \
    --portrait portrait.png \
    --circle-y 180 \
    --circle-radius 140 \
    -o cover.png
```

---

## 平台最佳尺寸

| 平台 | 比例 | 推荐像素 |
|------|------|----------|
| 小红书（推荐） | 3:4 竖版 | 1080×1440px |
| 小红书正方形 | 1:1 | 1080×1080px |
| 微信公众号封面 | 2.35:1 | 900×383px |
| 抖音封面 | 9:16 | 1080×1920px |

---

## 配色方案速查

| 风格 | 背景色 | 字体色 |
|------|--------|--------|
| 经典极简 | #FFFFFF | #000000 |
| 高级灰 | #F5F5F5 | #333333 |
| 治愈系 | #FFF8E7 | #5D4037 |
| 科技感 | #1A1A2E | 白/霓虹蓝 |
| 板书插画 | #FFFFFF | #000000 + #F5A623 |

---

## 使用统计

```bash
python scripts/nanobanana_draw.py --stats
```

---

## 故障排查

1. 确认 `OPENROUTER_API_KEY` 已设置
2. 检查网络连接
3. 确认 API key 有效且有额度

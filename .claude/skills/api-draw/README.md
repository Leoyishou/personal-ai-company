# Nanobanana 画图 Skill

一个专门用于 AI 画图的 Claude Code skill,通过 OpenRouter API 调用 Nanobanana (Google Gemini 3 Pro Image) 模型生成图片。

## 特点

- 专注于图片生成场景
- 支持中英文自然语言描述
- 简单易用的命令行接口
- 与 Claude Code 无缝集成
- 基于 Nanobanana 强大的图像生成能力

## 安装

### 1. 安装依赖

```bash
cd .claude/skills/nanobanana-draw
pip install -r scripts/requirements.txt
```

### 2. 配置 API Key

创建 `.env` 文件或设置环境变量:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## 使用方法

### 命令行使用

```bash
# 基础用法
python scripts/nanobanana_draw.py "画一只可爱的猫咪"

# 从标准输入读取
echo "画一幅山水画" | python scripts/nanobanana_draw.py

# 添加系统提示词
python scripts/nanobanana_draw.py \
  --system "你是专业的概念设计师" \
  "设计一个未来派的飞行器"

# 保存完整响应
python scripts/nanobanana_draw.py \
  "画一只小狗" \
  --output result.json
```

### 在 Claude Code 中使用

直接对 Claude 说:

```
画一只可爱的柴犬
帮我画一张产品界面
画一幅赛博朋克风格的城市夜景
```

Claude Code 会自动识别画图需求并调用此 skill。

## 配置选项

### 环境变量

- `OPENROUTER_API_KEY`: OpenRouter API 密钥 (必需)
- `NANOBANANA_MODEL`: 模型 ID (默认: `google/gemini-3-pro-image-preview`)
- `OPENROUTER_SITE_URL`: 你的网站 URL (可选,用于追踪)
- `OPENROUTER_APP_NAME`: 应用名称 (默认: `nanobanana-draw`)

### 命令行参数

- `prompt`: 画图描述 (位置参数或从 stdin 读取)
- `--system`: 系统提示词
- `--model`: 指定模型 ID
- `--temperature`: 采样温度 (默认: 0.7)
- `--max-tokens`: 最大 token 数
- `--print-json`: 输出完整 JSON 响应
- `--output`: 保存响应到文件

## 提示词技巧

### 好的提示词示例

```
画一只橘色的小猫,坐在窗台上看着窗外的雨,温馨的室内光线,水彩画风格
```

### 提示词要素

1. 主体描述:明确要画什么
2. 细节补充:姿态、环境、氛围
3. 风格指定:写实/卡通/水彩/赛博朋克等
4. 色调/光线:温暖/冷色/日落/柔和光线等

## 常见问题

### API Key 错误

确保正确设置了 `OPENROUTER_API_KEY` 环境变量:

```bash
echo $OPENROUTER_API_KEY
```

### 没有输出

检查:
1. API key 是否有效
2. 网络连接是否正常
3. 是否有足够的 API 额度

### 图片质量不满意

尝试:
1. 使用更详细的描述
2. 明确指定风格
3. 添加氛围和光线描述
4. 使用系统提示词引导模型

## 图片后处理工具

### 抠图工具 (remove_bg.py)

去除图片背景，支持白底抠图和 AI 智能抠图。

```bash
# 白底抠图（默认，适合头像/图标）
python scripts/remove_bg.py portrait.jpg -o portrait_nobg.png

# 调整阈值（更严格的白色判定）
python scripts/remove_bg.py portrait.jpg -o portrait_nobg.png --threshold 230

# AI智能抠图（需要 pip install rembg）
python scripts/remove_bg.py photo.jpg -o photo_nobg.png --mode ai
```

### 图片合成工具 (composite.py)

将前景图叠加到背景图上，支持预设位置和自定义坐标。

```bash
# 头像放右上角（默认）
python scripts/composite.py --bg whiteboard.jpg --fg portrait.png -o result.jpg

# 头像放右上角，缩放到150px
python scripts/composite.py --bg whiteboard.jpg --fg portrait.png --position top-right --size 150 -o result.jpg

# 自定义位置
python scripts/composite.py --bg whiteboard.jpg --fg portrait.png --x 700 --y 200 --size 120 -o result.jpg
```

预设位置：`top-left`, `top-right`, `bottom-left`, `bottom-right`, `center`

### 人物封面合成工具 (portrait_cover.py)

一步完成「白板 + 手绘圆框 + 头像」的精确合成。解决 AI 生成圆框位置不可控的问题。

**核心思路**：AI 生成不带圆框的白板图，圆框和头像由代码绘制，100% 可控对齐。

```bash
# 基础用法（使用默认参数）
python scripts/portrait_cover.py \
    --bg whiteboard.jpg \
    --portrait portrait.png \
    -o cover.png

# 自定义圆框位置和大小
python scripts/portrait_cover.py \
    --bg whiteboard.jpg \
    --portrait portrait.png \
    --circle-y 180 \
    --circle-radius 150 \
    --portrait-size 280 \
    -o cover.png

# 自定义圆框样式（更强的手绘感）
python scripts/portrait_cover.py \
    --bg whiteboard.jpg \
    --portrait portrait.png \
    --circle-color "#555555" \
    --circle-width 4 \
    --circle-passes 5 \
    -o cover.png
```

**关键参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--circle-y` | 圆心距顶部像素（X 自动居中） | 200 |
| `--circle-radius` | 圆框半径 | 140 |
| `--portrait-size` | 头像直径（应比圆框直径小 20px 左右） | 260 |
| `--circle-passes` | 绘制圈数（越多越有手绘感） | 3 |
| `--circle-wobble` | 抖动幅度 | 2 |

---

## 组合工作流：手绘白板 + 圆框头像

当需要生成"手绘白板 + 圆框中嵌入人物头像"这种组合图时，推荐使用以下工作流。

### 核心原则

**分离关注点**：
- AI 负责：生成白板内容（文字、图标、布局），顶部留白
- 代码负责：圆框 + 头像（精确可控，100% 对齐）

### 完整步骤

```bash
# Step 1: 生成头像（木版画风格，基于照片）
python scripts/nanobanana_draw.py "将这张照片中的人物转换为黑白线刻版画风格小头像：
- 人物面部用精细的黑白平行线条刻画，木刻版画质感
- 只保留头部和肩膀部分
- 纯白色背景
- 高对比度黑白线条
- 输出为正方形构图，1:1比例" \
    --image /tmp/person_photo.jpg \
    --style "线刻肖像" \
    --subject "人物名头像"

# Step 2: 生成手绘白板主图（顶部留白，不画圆框）
python scripts/nanobanana_draw.py "Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art.

IMPORTANT LAYOUT:
- TOP 300px area: completely EMPTY/WHITE (no circle, no frame, just blank space)
- Content starts below the blank area

Title: 「主标题」in bold hand-drawn style with blue underline.
Main content (vertical flow with arrows): ...

Style: Excalidraw hand-drawn aesthetic, wobbly imperfect lines." \
    --style "手绘白板" \
    --subject "主题"

# Step 3: 一键合成（圆框 + 头像，精确对齐）
python scripts/portrait_cover.py \
    --bg whiteboard.jpg \
    --portrait portrait.png \
    --circle-y 180 \
    --circle-radius 140 \
    --portrait-size 260 \
    -o final_cover.png
```

### 优势

| 对比项 | 旧方案（AI画圆框） | 新方案（代码画圆框） |
|--------|-------------------|---------------------|
| 圆框位置 | AI 随机，不可控 | 100% 精确 |
| 头像对齐 | 偏移、不居中 | 完美居中 |
| 手绘风格 | AI 可能画写实圆 | 代码模拟手绘抖动 |
| 迭代成本 | 整图重新生成 | 只需调参重新合成 |

---

## 技术架构

```
api-draw/
├── SKILL.md              # Skill 定义和说明
├── README.md             # 本文档
├── .env                  # 环境配置 (gitignore)
└── scripts/
    ├── nanobanana_draw.py    # AI画图主程序
    ├── nanobanana_client.py  # OpenRouter API 客户端
    ├── image_stitch.py       # 多图拼接工具
    ├── quote_portrait.py     # 人物语录卡片生成
    ├── remove_bg.py          # 抠图工具
    ├── circle_crop.py        # 圆形裁剪工具
    ├── composite.py          # 图片合成工具
    ├── portrait_cover.py     # 人物封面合成工具（圆框+头像）
    └── requirements.txt      # Python 依赖
```

## 开发

### 运行测试

```bash
python scripts/nanobanana_draw.py "测试prompt"
```

### 调试模式

```bash
python scripts/nanobanana_draw.py \
  "画一只猫" \
  --print-json
```

## 许可

MIT License

## 相关链接

- [OpenRouter 官网](https://openrouter.ai/)
- [Claude Code 文档](https://claude.com/claude-code)
- [Nanobanana 模型](https://openrouter.ai/google/gemini-3-pro-image-preview)

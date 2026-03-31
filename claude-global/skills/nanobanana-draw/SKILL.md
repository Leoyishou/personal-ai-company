---
name: nanobanana-draw
description: 使用 Nanobanana (Gemini 3 Pro Image) 生成图片,支持中英文描述、图片参考和风格迁移。
allowed-tools: Bash(python:*), Read, Write
---

# Nanobanana 画图工具

通过 OpenRouter API 调用 Nanobanana (Google Gemini 3 Pro Image) 模型生成图片。支持纯文字描述、图片参考和风格迁移。

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

### 基础使用（纯文字）

```bash
cd .claude/skills/nanobanana-draw
uv run python scripts/nanobanana_draw.py "画一只可爱的橘猫,坐在阳光下"
```

### 图片参考（单张图片+描述）

```bash
uv run python scripts/nanobanana_draw.py \
  "将这张照片中的人物转换成3D卡通风格" \
  --image photo.jpg
```

### 风格迁移（照片+风格参考图）

```bash
uv run python scripts/nanobanana_draw.py \
  "将第一张图片的人物转换成第二张图片的风格" \
  --image user_photo.jpg \
  --style-image cartoon_style.png
```

### 多图片参考

```bash
uv run python scripts/nanobanana_draw.py \
  "融合这两张图片的元素创作新图" \
  --image image1.jpg \
  --image image2.jpg
```

### 添加系统提示词

```bash
uv run python scripts/nanobanana_draw.py \
  --system "你是专业的插画师,擅长创作细节丰富的插画" \
  "画一只在森林里探险的小狐狸"
```

## 工作流建议

当用户请求画图时,遵循以下流程:

### Step 1: 理解画图需求

与用户确认:
- 画面主题和内容
- 风格偏好(写实/卡通/赛博朋克/水彩等)
- 特殊要求(色调/构图/细节等)

### Step 2: 组织 Prompt

基于用户需求构建详细的画图 prompt:
- 主体描述清晰
- 风格明确
- 氛围和细节丰富
- 使用中文或英文均可

### Step 3: 调用脚本

```bash
cd .claude/skills/nanobanana-draw
python scripts/nanobanana_draw.py "你的画图描述"
```

### Step 4: 返回结果

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

## 命令行参数

| 参数 | 说明 |
|------|------|
| `prompt` | 图片生成描述（必填） |
| `--image`, `-i` | 参考图片路径或URL（可多次使用） |
| `--style-image`, `-s` | 风格参考图片路径或URL |
| `--system` | 系统提示词 |
| `--model` | 模型ID |
| `--temperature` | 采样温度（默认0.7） |
| `--max-tokens` | 最大token数 |
| `--save-dir` | 图片保存目录 |
| `--no-save` | 不自动保存图片 |
| `--print-json` | 输出完整JSON |
| `--output` | 保存JSON到文件 |

## IP形象生成（配合 video-creator 使用）

生成3D卡通风格的数字人IP形象：

### 方式一：照片+风格图

```bash
uv run python scripts/nanobanana_draw.py \
  "将第一张图片中的人物转换成第二张图片的3D卡通风格，保持人物特征，正面半身像" \
  --image my_photo.jpg \
  --style-image cartoon_reference.png \
  --save-dir output/ip-avatar
```

### 方式二：照片+文字描述

```bash
uv run python scripts/nanobanana_draw.py \
  "将这张照片中的人物转换成3D皮克斯风格的卡通形象，大眼睛，精致五官，穿着米白色卫衣，戴透明眼镜，深蓝色科技感背景" \
  --image my_photo.jpg \
  --save-dir output/ip-avatar
```

## 技术细节

- 默认模型: `google/gemini-3-pro-image-preview`
- 支持通过 `--model` 参数切换模型
- Temperature 默认 0.7,可通过 `--temperature` 调整
- 支持 `--max-tokens` 限制输出长度
- 图片会自动转换为 base64 发送给 API
- 支持本地文件路径和 HTTP/HTTPS URL

## 故障排查

如果遇到问题:
1. 确认 OPENROUTER_API_KEY 已正确设置
2. 检查网络连接
3. 确认 API key 有效且有足够额度
4. 图片文件路径是否正确
5. 图片格式是否为 PNG/JPG/JPEG
6. 查看错误信息中的详细提示

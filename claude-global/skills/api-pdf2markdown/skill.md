---
name: mineru
description: "使用 MinerU 将 PDF 等文档转换为 Markdown/JSON 格式，支持表格、公式、图片提取，109 种语言 OCR。"
---

# MinerU 文档转换 Skill

将 PDF 等复杂文档转换为 LLM 可读的 Markdown/JSON 格式。

## 使用场景

- "把这个 PDF 转成 Markdown"
- "提取这份扫描件的内容"
- "解析这个 PDF 里的表格和公式"
- "OCR 识别这份文档"

## 核心能力

- 保留文档结构（标题、段落、列表）
- 提取表格（转 Markdown 表格）
- 提取公式（转 LaTeX）
- 提取图片及描述
- 支持 109 种语言 OCR
- 自动识别扫描件并启用 OCR

## 推荐用法：官方云 API

**精度最高，无需本地 GPU**

```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf --api
```

- 使用 VLM 模型，OmniDocBench 精度 90+
- 已内置 API Token，开箱即用
- 单文件限制：200MB / 600 页
- 每日配额：2000 页

## 本地处理

```bash
# Mac (CPU)
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf -b pipeline

# 有 GPU
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf -b hybrid-auto-engine
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--api` | 使用官方云 API | 否 |
| `-o` / `--output` | 输出目录 | `./mineru_output` |
| `-b` / `--backend` | 本地后端 | 自动选择 |
| `-l` / `--lang` | OCR 语言 | `ch` |
| `--token` | 自定义 API Token | 内置 |

## 后端精度对比

| 后端 | OmniDocBench 精度 | 环境要求 |
|------|------------------|----------|
| 云 API (VLM) | **90+** | 无 |
| `vlm-auto-engine` | 90+ | 强 GPU |
| `hybrid-auto-engine` | 90+ | GPU |
| `pipeline` | 82+ | CPU 可用 |

## 使用示例

1. **云 API 转换（推荐）**
```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf --api
```

2. **本地 CPU 转换**
```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf -b pipeline
```

3. **英文文档**
```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf -b pipeline -l en
```

4. **指定输出目录**
```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf -o ./output --api
```

## 输出说明

转换后在输出目录生成：
- `*.md` - Markdown 格式内容
- `images/` - 提取的图片
- `*_content_list.json` - 结构化 JSON 数据

## API Token 管理

内置 Token 有每日配额限制。如需更多配额，可在 [mineru.net](https://mineru.net/apiManage/token) 申请自己的 Token：

```bash
python3 ~/.claude/skills/mineru/scripts/convert.py document.pdf --api --token YOUR_TOKEN
```

## 注意事项

- 云 API 需要网络连接
- 本地首次运行会下载模型（约 2-3GB）
- Mac 本地处理务必使用 `-b pipeline`

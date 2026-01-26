---
name: openrouter-chat
description: 在本地通过 OpenRouter API 调用多模型，支持单轮/多轮消息、系统提示词和结构化输出。
allowed-tools: Bash(python:*), Read, Write
---

# OpenRouter 通用调用工具

将 OpenRouter API 封装为 Claude Code 可调用的本地 skill，用于 Nanobanana 作图、Gemini、GPT 模型的调用等场景。

## 快速开始

### 环境配置

设置 OpenRouter API key：

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

或创建 `.env` 文件（放在 skill 根目录）：

```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-3-pro-preview
OPENROUTER_SITE_URL=https://your-site.example
OPENROUTER_APP_NAME=openrouter-chat
```

可选配置：

```bash
export OPENROUTER_MODEL="google/gemini-3-pro-preview"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1/chat/completions"
export OPENROUTER_SITE_URL="https://your-site.example"
export OPENROUTER_APP_NAME="openrouter-chat"
```

### 基础使用

```bash
python scripts/openrouter_chat.py --prompt "用三句话解释向量数据库"
```

### 冒烟测试

```bash
python scripts/smoke_test.py
```

### 多轮消息

```bash
python scripts/openrouter_chat.py --messages messages.json
```

### 指定系统提示词与模型

```bash
python scripts/openrouter_chat.py \
  --system "你是资深产品经理" \
  --prompt "总结这段需求" \
  --model "anthropic/claude-sonnet-4.5"
```

### 常用模型（个人偏好）

- `google/gemini-3-pro-image-preview` (Nanobanana)
- `google/gemini-3-pro-preview`
- `anthropic/claude-sonnet-4.5`

## 工作流建议

当用户请求调用 OpenRouter 时，遵循以下流程：

### Step 1: 明确调用目标

与用户确认：
- 目标任务（总结/翻译/写作/代码生成等）
- 期望模型（可选）
- 输出格式（自然语言或 JSON）
- 是否需要系统提示词或上下文消息

### Step 2: 组织输入

根据场景选择输入方式：
- 单轮：`--prompt` 或管道输入
- 多轮：准备 `messages.json` 并使用 `--messages`
- 结构化输出：准备 `--extra` JSON 载荷（如 response_format）

### Step 3: 调用脚本

```bash
cd .claude/skills/openrouter-chat
python scripts/openrouter_chat.py --prompt "..."
```

### Step 4: 返回结果

输出模型回复，并按用户要求整理或格式化。

## 输出格式

- 默认：仅输出模型回复文本
- `--print-json`：输出完整 JSON
- `--output result.json`：保存完整响应

## 依赖安装

```bash
cd .claude/skills/openrouter-chat
pip install -r scripts/requirements.txt
```

## 开始使用

在 Claude Code 中直接说：

```
用 OpenRouter 生成一段产品介绍
用 Claude 3.5 Sonnet 翻译这段话
把这段需求整理成 JSON 结构
```

Claude 会调用该 skill 完成请求。

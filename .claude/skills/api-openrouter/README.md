# OpenRouter 调用 Skill

用于在本地通过 OpenRouter API 调用多模型的 Claude Code skill。

## 特性

✅ **通用模型调用** - 支持任何 OpenRouter 模型
✅ **单轮/多轮消息** - 通过 prompt 或 messages.json
✅ **系统提示词** - 直接传入 system role
✅ **结构化输出** - 支持额外 JSON 载荷
✅ **输出保存** - 可保存完整 JSON 响应

## 文件结构

```
openrouter-chat/
├── SKILL.md
├── README.md
├── API_REFERENCE.md
├── EXAMPLES.md
├── TROUBLESHOOTING.md
└── scripts/
    ├── openrouter_client.py
    ├── openrouter_chat.py
    └── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
cd .claude/skills/openrouter-chat
pip install -r scripts/requirements.txt
```

### 2. 配置 OpenRouter API Key

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

或使用 `.env` 文件（放在 skill 根目录）：

```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-3-pro-preview
OPENROUTER_SITE_URL=https://your-site.example
OPENROUTER_APP_NAME=openrouter-chat
```

可选配置：

```bash
export OPENROUTER_MODEL="google/gemini-3-pro-preview"
export OPENROUTER_SITE_URL="https://your-site.example"
export OPENROUTER_APP_NAME="openrouter-chat"
```

### 3. 运行示例

```bash
python scripts/openrouter_chat.py --prompt "用三句话解释向量数据库"
```

### 4. 冒烟测试

```bash
python scripts/smoke_test.py
```

常用模型（个人偏好）：
- `google/gemini-3-pro-image-preview` (Nanobanana)
- `google/gemini-3-pro-preview`
- `anthropic/claude-sonnet-4.5`

## 安装到 Claude Code

### 方法 1: 项目级安装

```bash
cp -r /path/to/openrouter-chat /your/project/.claude/skills/
```

### 方法 2: 用户级安装（推荐）

```bash
cp -r /path/to/openrouter-chat ~/.claude/skills/
```

## 使用方法

### Claude Code 自动调用

```
用 OpenRouter 生成一段产品介绍
用 Claude Sonnet 4.5 翻译这段话
把这段需求整理成 JSON 结构
```

### 直接调用脚本

```bash
python scripts/openrouter_chat.py \
  --system "你是资深产品经理" \
  --prompt "请整理核心功能" \
  --model "anthropic/claude-sonnet-4.5" \
  --temperature 0.3
```

更多示例见 [EXAMPLES.md](EXAMPLES.md)

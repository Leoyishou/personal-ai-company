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

## 技术架构

```
nanobanana-draw/
├── SKILL.md              # Skill 定义和说明
├── README.md             # 本文档
├── .env                  # 环境配置 (gitignore)
└── scripts/
    ├── nanobanana_draw.py    # 主程序
    ├── nanobanana_client.py  # API 客户端
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

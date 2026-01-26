# OpenRouter API 参考文档

## 目录

- [核心函数](#核心函数)
- [环境变量配置](#环境变量配置)
- [命令行工具](#命令行工具)
- [消息结构](#消息结构)

---

## 核心函数

### request_openrouter()

调用 OpenRouter API 进行模型推理。

**参数**:
```python
request_openrouter(
    model,                # 模型名称
    messages,             # 消息列表
    api_key=None,         # OpenRouter API Key
    base_url=None,        # API 端点
    temperature=0.7,      # 温度
    max_tokens=None,      # 输出 token 上限
    timeout=90,           # 超时时间
    extra_payload=None,   # 额外 payload 字段
)
```

**返回值**: `(content, raw_json)`

**异常**:
- `ValueError`: 缺少 API Key 或消息结构错误
- `RuntimeError`: API 响应异常

---

## 环境变量配置

| 变量名 | 说明 | 必需 |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter API Key | ✅ |
| `OPENROUTER_MODEL` | 默认模型 | 否 |
| `OPENROUTER_BASE_URL` | API 地址 | 否 |
| `OPENROUTER_SITE_URL` | Referer | 否 |
| `OPENROUTER_APP_NAME` | 应用名称 | 否 |

支持在 skill 根目录放置 `.env` 文件自动加载。

---

## 命令行工具

`scripts/openrouter_chat.py` 用于直接调用模型。

**参数**:
- `--prompt`：单轮用户输入
- `--prompt-file`：从文件读取 prompt
- `--messages`：多轮消息 JSON 文件
- `--system`：系统提示词
- `--model`：模型名称
- `--temperature`：温度
- `--max-tokens`：输出上限
- `--extra`：额外 payload（JSON 文件）
- `--print-json`：输出完整 JSON
- `--output`：保存完整 JSON

---

## 消息结构

OpenRouter 消息示例：

```json
[
  {"role": "system", "content": "你是资深产品经理"},
  {"role": "user", "content": "总结这段需求"}
]
```

保存为 `messages.json` 后使用：

```bash
python scripts/openrouter_chat.py --messages messages.json
```

# OpenRouter Skill 示例

## 示例 1：产品文案生成

```bash
python scripts/openrouter_chat.py \
  --prompt "为一款 AI 写作工具写 3 句产品介绍" \
  --model "google/gemini-3-pro-preview"
```

## 示例 2：翻译任务

```bash
python scripts/openrouter_chat.py \
  --system "你是资深翻译" \
  --prompt "将下面内容翻译成英文：今天我们发布新版本" \
  --model "anthropic/claude-sonnet-4.5"
```

## 示例 3：结构化输出

准备 `extra.json`：

```json
{
  "response_format": {
    "type": "json_object"
  }
}
```

调用：

```bash
python scripts/openrouter_chat.py \
  --prompt "把这段需求整理成 JSON: 需要支持登录、个人资料和订单列表" \
  --extra extra.json
```

## 示例 4：多轮上下文

`messages.json`：

```json
[
  {"role": "system", "content": "你是专业面试官"},
  {"role": "user", "content": "请问如何解释缓存击穿？"},
  {"role": "assistant", "content": "..."},
  {"role": "user", "content": "再补充一些真实案例"}
]
```

调用：

```bash
python scripts/openrouter_chat.py --messages messages.json
```

## 示例 5：冒烟测试

```bash
python scripts/smoke_test.py
```

预期输出：

```
ok
```

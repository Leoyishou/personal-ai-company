# API 参考文档

本文档详细说明 Nanobanana 画图 skill 的 API 接口和使用方法。

## 命令行接口

### nanobanana_draw.py

主程序入口,用于生成图片。

#### 语法

```bash
python scripts/nanobanana_draw.py [prompt] [options]
```

#### 参数

##### 位置参数

- `prompt` (可选): 画图描述文本
  - 如果不提供,将从标准输入 (stdin) 读取
  - 类型: 字符串
  - 示例: `"画一只可爱的猫"`

##### 可选参数

- `--system TEXT`
  - 系统提示词,用于引导模型风格或视角
  - 类型: 字符串
  - 默认: 无
  - 示例: `"你是专业的插画师"`

- `--model MODEL_ID`
  - 指定使用的模型 ID
  - 类型: 字符串
  - 默认: `google/gemini-3-pro-image-preview` (Nanobanana)
  - 示例: `--model "google/gemini-3-pro-image-preview"`

- `--temperature FLOAT`
  - 控制生成的随机性
  - 类型: 浮点数
  - 范围: 0.0 - 2.0
  - 默认: 0.7
  - 说明:
    - 较低值(如 0.3): 更确定、一致的输出
    - 较高值(如 1.0): 更多样、创意的输出

- `--max-tokens INT`
  - 限制生成的最大 token 数
  - 类型: 整数
  - 默认: 模型默认值
  - 说明: 通常不需要设置,除非需要限制输出长度

- `--print-json`
  - 输出完整的 JSON 响应而不是仅输出内容
  - 类型: 布尔标志
  - 默认: False

- `--output PATH`
  - 将完整的 JSON 响应保存到文件
  - 类型: 文件路径
  - 默认: 不保存
  - 示例: `--output result.json`

#### 返回值

- **成功**:
  - 默认: 输出模型生成的内容到 stdout
  - `--print-json`: 输出完整 JSON 到 stdout
  - `--output`: 保存完整 JSON 到指定文件

- **失败**:
  - 返回非零退出码
  - 错误信息输出到 stderr

#### 示例

```bash
# 基础用法
python scripts/nanobanana_draw.py "画一只猫"

# 使用系统提示词
python scripts/nanobanana_draw.py \
  --system "你是专业摄影师" \
  "拍一张风景照"

# 调整温度
python scripts/nanobanana_draw.py \
  --temperature 0.9 \
  "创作一幅抽象画"

# 保存响应
python scripts/nanobanana_draw.py \
  "画一只狗" \
  --output result.json

# 从 stdin 读取
echo "画一幅山水画" | python scripts/nanobanana_draw.py
```

## Python API

### nanobanana_client 模块

提供底层 API 客户端功能。

#### generate_image()

生成图片的核心函数。

##### 签名

```python
def generate_image(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = 90,
    system_prompt: Optional[str] = None,
) -> Tuple[str, dict]:
```

##### 参数

- `prompt` (str, 必需): 画图描述文本
- `model` (str, 可选): 模型 ID,默认为 `DEFAULT_NANOBANANA_MODEL`
- `api_key` (str, 可选): OpenRouter API key,默认从环境变量读取
- `base_url` (str, 可选): API endpoint,默认为 OpenRouter 标准 endpoint
- `temperature` (float, 可选): 采样温度,默认 0.7
- `max_tokens` (int, 可选): 最大 token 数,默认为 None
- `timeout` (int, 可选): 请求超时时间(秒),默认 90
- `system_prompt` (str, 可选): 系统提示词

##### 返回值

返回一个元组 `(content, raw_json)`:
- `content` (str): 模型生成的内容
- `raw_json` (dict): 完整的 API 响应

##### 异常

- `ValueError`: 参数验证失败(如缺少 API key、空 prompt 等)
- `RuntimeError`: API 请求失败(如认证失败、模型不可用等)
- `requests.exceptions.Timeout`: 请求超时
- `requests.exceptions.ConnectionError`: 网络连接失败

##### 示例

```python
from nanobanana_client import generate_image

# 基础用法
content, raw = generate_image("画一只猫")
print(content)

# 完整参数
content, raw = generate_image(
    prompt="画一只可爱的柴犬",
    model="google/gemini-3-pro-image-preview",
    temperature=0.8,
    max_tokens=1000,
    system_prompt="你是专业的插画师"
)

# 处理完整响应
print(f"模型: {raw['model']}")
print(f"内容: {content}")
print(f"使用的 tokens: {raw['usage']}")
```

#### 辅助函数

##### resolve_api_key()

```python
def resolve_api_key(api_key: Optional[str] = None) -> str:
```

从参数或环境变量解析 API key。

##### build_headers()

```python
def build_headers(
    api_key: str,
    app_name: Optional[str] = None,
    site_url: Optional[str] = None
) -> dict:
```

构建 OpenRouter 请求头。

##### normalize_messages()

```python
def normalize_messages(messages: list) -> list:
```

验证并规范化消息列表。

## 环境变量

### OPENROUTER_API_KEY

- **必需**: 是
- **类型**: 字符串
- **说明**: OpenRouter API 密钥
- **示例**: `sk-or-v1-...`
- **获取**: [OpenRouter 网站](https://openrouter.ai/)

### NANOBANANA_MODEL

- **必需**: 否
- **类型**: 字符串
- **默认**: `google/gemini-3-pro-image-preview`
- **说明**: 默认使用的模型 ID
- **示例**: `google/gemini-3-pro-image-preview`

### OPENROUTER_BASE_URL

- **必需**: 否
- **类型**: 字符串
- **默认**: `https://openrouter.ai/api/v1/chat/completions`
- **说明**: OpenRouter API endpoint
- **用途**: 通常不需要修改,除非使用自定义代理

### OPENROUTER_SITE_URL

- **必需**: 否
- **类型**: 字符串
- **默认**: 无
- **说明**: 你的网站 URL,用于 OpenRouter 追踪和统计
- **示例**: `https://your-site.example`

### OPENROUTER_APP_NAME

- **必需**: 否
- **类型**: 字符串
- **默认**: `nanobanana-draw`
- **说明**: 应用名称,用于 OpenRouter 追踪
- **示例**: `my-drawing-app`

## 响应格式

### 标准输出 (默认)

仅输出模型生成的内容:

```
这是一张可爱的橘色小猫的图片,它坐在阳光洒满的窗台上...
```

### JSON 输出 (--print-json)

完整的 API 响应:

```json
{
  "id": "gen-...",
  "model": "google/gemini-3-pro-image-preview",
  "object": "chat.completion",
  "created": 1234567890,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "这是一张可爱的橘色小猫的图片..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  }
}
```

## 退出码

- `0`: 成功
- `1`: 一般错误(参数错误、API 调用失败等)
- `2`: 命令行参数解析错误

## 输入/输出

### 标准输入 (stdin)

如果没有提供 `prompt` 参数,程序会从 stdin 读取:

```bash
echo "画一只猫" | python scripts/nanobanana_draw.py
cat prompt.txt | python scripts/nanobanana_draw.py
```

### 标准输出 (stdout)

- 默认: 输出模型生成的内容
- `--print-json`: 输出完整 JSON

### 标准错误 (stderr)

所有错误信息输出到 stderr:
- 参数验证错误
- API 调用错误
- 网络错误等

### 文件输出

使用 `--output` 将完整响应保存到文件:

```bash
python scripts/nanobanana_draw.py \
  "画一只猫" \
  --output result.json
```

## 性能考虑

### 超时设置

默认超时为 90 秒。对于复杂的画图请求,可能需要更长时间。

### 速率限制

遵循 OpenRouter 的速率限制:
- 取决于你的账户类型
- 建议在批量请求时添加延迟

### Token 使用

- Prompt tokens: 取决于输入的长度
- Completion tokens: 取决于模型输出的长度
- 使用 `--max-tokens` 可以限制输出长度以节省成本

## 最佳实践

### 1. 错误处理

```python
from nanobanana_client import generate_image

try:
    content, raw = generate_image("画一只猫")
    print(content)
except ValueError as e:
    print(f"参数错误: {e}")
except RuntimeError as e:
    print(f"API 错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 2. 重试逻辑

```python
import time
from nanobanana_client import generate_image

def generate_with_retry(prompt, max_retries=3):
    for i in range(max_retries):
        try:
            return generate_image(prompt)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 指数退避
```

### 3. 批量处理

```python
from nanobanana_client import generate_image
import time

prompts = ["画一只猫", "画一只狗", "画一只鸟"]

for prompt in prompts:
    content, _ = generate_image(prompt)
    print(f"{prompt}: {content}")
    time.sleep(1)  # 避免触发速率限制
```

## 版本历史

### v1.0.0
- 初始版本
- 支持基础画图功能
- 支持系统提示词
- 支持从 stdin 读取
- 支持 JSON 输出

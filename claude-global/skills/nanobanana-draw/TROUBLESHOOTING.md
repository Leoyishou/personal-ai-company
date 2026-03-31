# 故障排查指南

本文档帮助你解决使用 Nanobanana 画图 skill 时可能遇到的问题。

## 常见错误

### 1. API Key 错误

**错误信息:**
```
ValueError: Missing OPENROUTER_API_KEY
```

**原因:** 未设置 OpenRouter API key

**解决方案:**
```bash
# 方法 1: 设置环境变量
export OPENROUTER_API_KEY="sk-or-v1-..."

# 方法 2: 创建 .env 文件
cd .claude/skills/nanobanana-draw
echo 'OPENROUTER_API_KEY=sk-or-v1-...' > .env

# 验证设置
echo $OPENROUTER_API_KEY
```

### 2. 认证失败

**错误信息:**
```
RuntimeError: OpenRouter request failed (401): {"error": "Invalid API key"}
```

**原因:** API key 无效或已过期

**解决方案:**
1. 检查 API key 是否正确
2. 访问 [OpenRouter](https://openrouter.ai/) 验证或重新生成 key
3. 确认没有多余的空格或引号

### 3. 额度不足

**错误信息:**
```
RuntimeError: OpenRouter request failed (402): {"error": "Insufficient credits"}
```

**原因:** OpenRouter 账户余额不足

**解决方案:**
1. 登录 OpenRouter 账户
2. 充值或检查账户余额
3. 查看当前的使用情况

### 4. 模型不可用

**错误信息:**
```
RuntimeError: OpenRouter request failed (404): {"error": "Model not found"}
```

**原因:** 指定的模型 ID 不存在或不可用

**解决方案:**
```bash
# 使用默认的 Nanobanana 模型
python scripts/nanobanana_draw.py "画一只猫"

# 或明确指定模型
python scripts/nanobanana_draw.py \
  --model "google/gemini-3-pro-image-preview" \
  "画一只猫"
```

### 5. 网络连接问题

**错误信息:**
```
requests.exceptions.ConnectionError: Failed to establish connection
```

**原因:** 网络连接失败

**解决方案:**
1. 检查网络连接
2. 确认可以访问 openrouter.ai
3. 检查防火墙或代理设置
4. 如果使用代理,设置相应的环境变量:
```bash
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

### 6. 超时错误

**错误信息:**
```
requests.exceptions.Timeout: Request timed out
```

**原因:** 请求超时(默认 90 秒)

**解决方案:**
1. 检查网络速度
2. 重试请求
3. 如果是复杂的画图请求,这可能是正常的,等待时间可能较长

### 7. 依赖缺失

**错误信息:**
```
ModuleNotFoundError: No module named 'requests'
```

**原因:** Python 依赖未安装

**解决方案:**
```bash
cd .claude/skills/nanobanana-draw
pip install -r scripts/requirements.txt

# 或单独安装
pip install requests python-dotenv
```

### 8. 权限错误

**错误信息:**
```
PermissionError: [Errno 13] Permission denied
```

**原因:** 文件权限问题

**解决方案:**
```bash
# 给脚本添加执行权限
chmod +x scripts/nanobanana_draw.py

# 或使用 python 直接运行
python scripts/nanobanana_draw.py "prompt"
```

### 9. 空 Prompt 错误

**错误信息:**
```
ValueError: Prompt cannot be empty
```

**原因:** 没有提供画图描述

**解决方案:**
```bash
# 提供 prompt 作为参数
python scripts/nanobanana_draw.py "画一只猫"

# 或从 stdin 读取
echo "画一只猫" | python scripts/nanobanana_draw.py
```

### 10. JSON 解析错误

**错误信息:**
```
json.JSONDecodeError: Expecting value
```

**原因:** API 返回了非 JSON 格式的响应

**解决方案:**
1. 检查 API 状态
2. 使用 `--print-json` 查看完整响应
3. 重试请求

## 调试技巧

### 1. 启用详细输出

```bash
python scripts/nanobanana_draw.py \
  "画一只猫" \
  --print-json
```

### 2. 保存响应用于分析

```bash
python scripts/nanobanana_draw.py \
  "画一只猫" \
  --output debug.json

# 查看响应
cat debug.json | python -m json.tool
```

### 3. 检查环境变量

```bash
# 检查所有相关环境变量
env | grep OPENROUTER
env | grep NANOBANANA
```

### 4. 测试网络连接

```bash
# 测试能否访问 OpenRouter API
curl -I https://openrouter.ai/api/v1/chat/completions
```

### 5. 验证 API Key

```bash
# 使用 curl 测试 API key
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## 性能问题

### 响应速度慢

**可能原因:**
1. 网络速度慢
2. Nanobanana 模型处理复杂的画图请求需要时间
3. OpenRouter 服务器负载高

**优化建议:**
1. 简化画图描述
2. 确保网络连接稳定
3. 在网络条件好的时候使用

### 输出质量不佳

**可能原因:**
1. Prompt 描述不够详细
2. 风格指定不明确
3. 模型理解有偏差

**优化建议:**
1. 使用更详细的描述
2. 参考 EXAMPLES.md 中的提示词模板
3. 添加系统提示词引导模型
4. 多次尝试不同的表述方式

## 环境问题

### Python 版本

确保使用 Python 3.7+:
```bash
python --version
```

### 虚拟环境

建议使用虚拟环境:
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r scripts/requirements.txt
```

## 获取帮助

如果以上方法都无法解决你的问题:

1. **查看文档:**
   - README.md - 基础使用说明
   - EXAMPLES.md - 使用示例
   - API_REFERENCE.md - API 参考

2. **检查日志:**
   - 查看完整的错误堆栈
   - 使用 `--print-json` 查看 API 响应

3. **社区支持:**
   - OpenRouter Discord/论坛
   - Claude Code GitHub Issues

4. **联系支持:**
   - OpenRouter 支持: [OpenRouter Support](https://openrouter.ai/support)

## 快速诊断清单

遇到问题时,按以下清单逐项检查:

- [ ] API key 是否已设置且有效
- [ ] 依赖是否已安装 (`pip list | grep requests`)
- [ ] 网络连接是否正常
- [ ] Prompt 是否提供且非空
- [ ] Python 版本是否 3.7+
- [ ] 账户余额是否充足
- [ ] 模型 ID 是否正确
- [ ] 文件权限是否正确

## 报告 Bug

如果你发现了 bug,请提供以下信息:

1. 完整的错误信息和堆栈跟踪
2. 使用的命令和参数
3. Python 版本
4. 操作系统
5. 相关的环境变量设置(隐藏敏感信息)
6. 使用 `--print-json` 的输出(隐藏敏感信息)

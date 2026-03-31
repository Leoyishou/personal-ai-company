# 故障排查

## 1. 提示缺少 OPENROUTER_API_KEY

**原因**: 未设置环境变量。

**解决**:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

## 2. 请求返回 401/403

**原因**: API Key 无效或权限不足。

**解决**:
- 在 https://openrouter.ai/keys 重新生成 API Key
- 确认 key 已加入到环境变量

## 3. 报错 response missing choices

**原因**: OpenRouter 返回异常格式。

**解决**:
- 检查 `OPENROUTER_BASE_URL`
- 尝试降低 `temperature`
- 使用 `--print-json` 查看原始响应

## 4. 模型不可用

**原因**: 模型名称错误或未开通。

**解决**:
- 在 https://openrouter.ai/models 查看可用模型
- 使用 `--model` 指定正确名称

## 5. 网络连接失败

**原因**: 本地网络限制或代理配置问题。

**解决**:
- 检查网络连接
- 确认系统代理设置
- 尝试使用 VPN 或企业网络

## 6. 快速冒烟测试

运行：

```bash
python scripts/smoke_test.py
```

若输出 `ok` 说明 API 调用正常。

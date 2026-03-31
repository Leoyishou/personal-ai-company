---
name: use-my-phone
description: Use when needing to control the real iPhone - open apps, tap, swipe, screenshot, extract data via OCR. Triggers: "打开手机app"、"在iPhone上操作"、"真机自动化"
---

# Use My Phone

通过 WDA (WebDriverAgent) 控制真机 iPhone，实现 App 自动化。

## 前提条件

| 条件 | 状态检查 |
|------|----------|
| iPhone 解锁并亮屏 | 手动确认 |
| WDA 运行中 | `curl -s http://localhost:8100/status` 返回 `"ready": true` |
| 端口转发 | `iproxy 8100 8100 -u 00008140-000A28A81ABB001C &` |

**如果 WDA 未运行：** 提醒用户在 Xcode 中按 Cmd+U 启动 WebDriverAgentRunner。

## 设备信息

```
UDID: 00008140-000A28A81ABB001C
型号: iPhone 16 Pro Max
屏幕: 440x956 (逻辑像素)
```

## 核心 API

所有操作通过 WDA REST API (`http://localhost:8100`)：

### 创建 Session（启动 App）

```python
import requests
import base64

WDA = "http://localhost:8100"

def create_session(bundle_id):
    data = {"capabilities": {"alwaysMatch": {"bundleId": bundle_id}}}
    resp = requests.post(f"{WDA}/session", json=data)
    return resp.json().get("sessionId")

# 常用 Bundle ID
# com.tencent.QQMusic - QQ音乐
# com.tencent.xin - 微信
# com.apple.mobilesafari - Safari
```

### 截图

```python
def screenshot(session_id, path):
    resp = requests.get(f"{WDA}/session/{session_id}/screenshot")
    img = base64.b64decode(resp.json()["value"])
    with open(path, "wb") as f:
        f.write(img)
```

### 点击（W3C Actions API）

```python
def tap(session_id, x, y):
    actions = {
        "actions": [{
            "type": "pointer",
            "id": "finger1",
            "parameters": {"pointerType": "touch"},
            "actions": [
                {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                {"type": "pointerDown", "button": 0},
                {"type": "pause", "duration": 100},
                {"type": "pointerUp", "button": 0}
            ]
        }]
    }
    requests.post(f"{WDA}/session/{session_id}/actions", json=actions)
```

### 滑动

```python
def swipe(session_id, start_x, start_y, end_x, end_y, duration=500):
    actions = {
        "actions": [{
            "type": "pointer",
            "id": "finger1",
            "parameters": {"pointerType": "touch"},
            "actions": [
                {"type": "pointerMove", "duration": 0, "x": start_x, "y": start_y},
                {"type": "pointerDown", "button": 0},
                {"type": "pointerMove", "duration": duration, "x": end_x, "y": end_y},
                {"type": "pointerUp", "button": 0}
            ]
        }]
    }
    requests.post(f"{WDA}/session/{session_id}/actions", json=actions)
```

### 输入文本

```python
def type_text(session_id, text):
    # 先点击输入框，然后发送文本
    requests.post(f"{WDA}/session/{session_id}/wda/keys", json={"value": list(text)})
```

### 关闭 Session

```python
def close_session(session_id):
    requests.delete(f"{WDA}/session/{session_id}")
```

## 典型工作流

```python
# 1. 检查 WDA
status = requests.get(f"{WDA}/status").json()
if not status.get("value", {}).get("ready"):
    print("WDA 未运行，请在 Xcode 按 Cmd+U")
    exit(1)

# 2. 启动 App
session = create_session("com.tencent.QQMusic")

# 3. 等待 App 加载
time.sleep(3)

# 4. 截图查看当前状态
screenshot(session, "/tmp/current.png")

# 5. 执行操作（点击、滑动等）
tap(session, 220, 500)

# 6. 关闭
close_session(session)
```

## 常见问题

| 错误 | 解决方案 |
|------|----------|
| "device was locked" | 解锁 iPhone 并保持亮屏 |
| "session not created" | iPhone 锁屏了，解锁后重试 |
| 点击无效 | 检查坐标是否正确（截图确认） |
| WDA 无响应 | 重新在 Xcode 运行 Cmd+U |

## 启动端口转发

```bash
# 杀掉旧进程并启动新的
pkill -f "iproxy 8100" 2>/dev/null
iproxy 8100 8100 -u 00008140-000A28A81ABB001C &
```

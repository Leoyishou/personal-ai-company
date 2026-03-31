# Computer Use - AI 自动操作电脑

使用 Simular AI 的 Agent S 框架，让 AI 像人类一样操作电脑 GUI，自动完成复杂任务。

## 触发条件

用户要求以下任务时触发：
- "帮我操作电脑..."
- "自动化操作..."
- "打开 XX 应用然后..."
- "用 computer use 做..."
- "帮我点击/输入/填写..."
- 任何需要 GUI 自动化的任务

## 使用方法

### 快速启动

在终端中运行：
```bash
~/.claude/skills/computer-use/run.sh
```

启动后会显示 `Query:` 提示符，输入你想让 AI 完成的任务，例如：
- "打开 Safari 并搜索天气"
- "打开系统设置，进入蓝牙设置"
- "打开微信，给张三发一条消息"

### 指定模型

```bash
~/.claude/skills/computer-use/run.sh claude-3-5-sonnet-20241022  # 默认
~/.claude/skills/computer-use/run.sh gpt-4o                       # 使用 GPT-4o
```

## 环境配置

已配置好以下 API Key：
- **ANTHROPIC_API_KEY** - 用于 Claude 模型推理
- **OPENROUTER_API_KEY** - 用于 Embedding（通过 OpenRouter 调用 text-embedding-3-small）

虚拟环境路径：`/Users/liuyishou/usr/projects/inbox/agent-s-env`

## 首次使用前提

1. **辅助功能权限**：系统设置 > 隐私与安全 > 辅助功能 > 允许终端/Warp
2. **屏幕录制权限**：系统设置 > 隐私与安全 > 屏幕录制 > 允许终端/Warp
3. **自动化权限**：系统设置 > 隐私与安全 > 自动化 > 终端/Warp > System Events

## 注意事项

- Agent S 会控制鼠标和键盘，运行时请勿操作电脑
- 建议在单显示器环境下使用
- 每个操作前会弹出确认对话框，点击 OK 继续
- 任务完成后会弹出 "Task Completed" 提示

## 工作原理

1. 截取屏幕截图
2. 获取当前 UI 元素树（Accessibility Tree）
3. Claude 分析界面并生成 pyautogui 代码
4. 执行代码操作鼠标/键盘
5. 循环直到任务完成

## 参考链接

- GitHub: https://github.com/simular-ai/Agent-S
- 论文: ICLR 2025

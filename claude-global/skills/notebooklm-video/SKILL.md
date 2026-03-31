# NotebookLM 视频生成

用 NotebookLM 的 AI 视频功能，将笔记本内容生成讲解视频。

## 触发条件

- 用户提到 "NotebookLM 视频"
- 用户想用 NotebookLM 生成视频
- 用户想下载 NotebookLM 的视频

## 前置依赖

依赖 `notebooklm` skill 的浏览器认证和 profile。确保已完成 NotebookLM 认证：

```bash
cd ~/.claude/skills/notebooklm && python scripts/run.py auth_manager.py status
```

## 使用方法

### 生成视频

```bash
cd ~/.claude/skills/notebooklm-video && python scripts/generate_video.py --notebook-url "https://notebooklm.google.com/notebook/xxx"
```

或使用 notebook ID（需要先在 notebooklm skill 中添加笔记本）：

```bash
cd ~/.claude/skills/notebooklm-video && python scripts/generate_video.py --notebook-id "红楼梦"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--notebook-url` | NotebookLM 笔记本 URL |
| `--notebook-id` | notebooklm skill library 中的笔记本 ID |
| `--output-dir` | 视频保存目录，默认 ~/Downloads |
| `--wait-timeout` | 等待生成超时时间（分钟），默认 15 |
| `--show-browser` | 显示浏览器窗口（调试用） |

## 注意事项

1. **视频生成时间**：取决于笔记本内容量，通常需要 5-15 分钟
2. **不要关闭浏览器**：脚本运行时会弹出浏览器窗口，请勿手动关闭
3. **免费账户限制**：NotebookLM 免费版每天有视频生成次数限制
4. **网络要求**：需要稳定的网络连接

## 工作流程

1. 打开笔记本 URL
2. 点击 Studio 面板的 "Video" 按钮
3. 触发视频生成
4. 轮询检查生成状态（每 30 秒）
5. 生成完成后自动下载到指定目录

## 示例

```bash
# 为红楼梦笔记本生成视频
python scripts/generate_video.py --notebook-url "https://notebooklm.google.com/notebook/4bc28826-131e-40d4-86e0-c651ed1b1975" --output-dir ~/Videos

# 使用 library 中的笔记本
python scripts/generate_video.py --notebook-id "红楼梦"
```

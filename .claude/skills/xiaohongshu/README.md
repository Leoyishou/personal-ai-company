# 小红书发布 Skill

基于 **小红书 MCP (Model Context Protocol)** 快速发布内容到小红书的 Claude Code skill。

通过简单的对话即可发布图文笔记和视频笔记，无需手动操作小红书 APP。

## 特性

✅ **快速发布** - 通过 Claude Code 对话即可发布内容
✅ **图文支持** - 支持多图发布，本地路径或 URL
✅ **视频支持** - 支持视频笔记发布
✅ **参数验证** - 自动检查标题、内容长度限制
✅ **内容优化** - 提供内容创作建议和最佳实践
✅ **易于使用** - 无需编写代码，对话即可完成

## 文件结构

```
xiaohongshu/
├── SKILL.md          # 核心 skill 定义和工作流指令
├── README.md         # 本文件（用户文档）
└── EXAMPLES.md       # 使用示例（可选）
```

## 快速开始

### 1. 安装小红书 MCP 服务

首先需要安装并启动小红书 MCP 服务：

```bash
# 克隆项目
git clone https://github.com/xpzouying/xiaohongshu-mcp
cd xiaohongshu-mcp

# 启动服务（默认无头模式，后台运行）
go run .

# 如需查看浏览器界面（调试时使用）
go run . -headless=false
```

服务启动后会在 `http://localhost:18060/mcp` 监听。

### 2. 将 MCP 服务添加到 Claude Code

```bash
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp
```

验证是否添加成功：

```bash
claude mcp list
```

应该能看到 `xiaohongshu-mcp` 在列表中。

### 3. 安装 Skill

**方法 1: 用户级安装（推荐）**

所有项目都能使用这个 skill：

```bash
# macOS / Linux
cp -r xiaohongshu ~/.claude/skills/

# Windows
xcopy xiaohongshu %USERPROFILE%\.claude\skills\xiaohongshu\ /E /I
```

**方法 2: 项目级安装**

仅在当前项目使用：

```bash
cp -r xiaohongshu /your/project/.claude/skills/
```

### 4. 登录小红书

首次使用需要登录。在 Claude Code 中说：

```
请帮我登录小红书
```

Claude 会自动：
1. 检查登录状态
2. 如果未登录，获取登录二维码
3. 将二维码保存为 `xiaohongshu_login_qrcode.png` 到当前工作目录
4. 提示你用小红书 App 扫码登录

扫码完成后，告诉 Claude "已扫码登录"，它会确认登录状态。

### 5. 开始发布

在 Claude Code 中说：

```
帮我发一篇小红书笔记：
标题：我的日常穿搭
内容：今天分享一套简约风穿搭，上衣是白色衬衫...
图片：/Users/liuyishou/Pictures/outfit1.jpg
```

## 使用方法

### 在 Claude Code 中使用

Claude Code 会根据你的请求自动使用这个 skill。以下是一些示例：

**发布图文笔记：**
```
发一篇小红书笔记，标题是"美食推荐"，内容是介绍本地美食
```

**发布视频笔记：**
```
帮我发布一个视频到小红书：
标题：旅行 Vlog
内容：分享我的旅行见闻
视频：/Users/liuyishou/Videos/travel.mp4
```

**登录账号：**
```
登录小红书
```

### 功能说明

#### 1. 发布图文笔记

**参数要求：**
- **标题**：最多 20 个字符
- **内容**：最多 1000 个字符
- **图片**：支持本地路径（推荐）或 HTTP/HTTPS URL

**示例：**
```
发布小红书图文：
标题：三亚旅行攻略
内容：这次去三亚玩了5天4夜，整理了一份超详细的攻略...（可以写很长）
图片：
- /Users/liuyishou/Pictures/sanya1.jpg
- /Users/liuyishou/Pictures/sanya2.jpg
- https://example.com/sanya3.jpg
```

#### 2. 发布视频笔记

**参数要求：**
- **标题**：最多 20 个字符
- **内容**：最多 1000 个字符
- **视频**：必须是本地绝对路径（不支持 URL）
- **文件大小**：建议小于 1GB

**示例：**
```
发布小红书视频：
标题：美食教程
内容：教你做简单又美味的意大利面，食材准备...
视频：/Users/liuyishou/Videos/cooking.mp4
```

#### 3. 登录管理

```
登录小红书
```

**登录流程：**
- Claude 会获取登录二维码并保存为 `xiaohongshu_login_qrcode.png`
- 用小红书 App 扫码登录
- 登录信息会被保存，后续发布无需重复登录
- 二维码有效期约 5 分钟，过期后需重新获取

**切换账号：**
```
请帮我切换小红书账号
```
Claude 会删除当前登录信息，然后重新获取二维码。

## 工作流程

当你请求发布小红书内容时，Claude 会自动：

1. **检查登录状态** - 如未登录，引导你完成登录
2. **收集内容信息** - 确认标题、正文、媒体文件
3. **验证参数** - 检查标题和内容长度，验证文件路径
4. **优化建议** - 如有需要，提供内容优化建议
5. **调用 MCP 发布** - 使用小红书 MCP 工具完成发布
6. **返回结果** - 告知发布结果，如有链接则提供

## 最佳实践

### 内容创作建议

**标题优化（20 字以内）：**
- ✅ "三亚5日游攻略｜省钱版"
- ✅ "新手化妆教程｜超详细"
- ❌ "我的三亚旅行日记，玩了好多地方，很开心"（太长）

**正文结构（1000 字以内）：**
```
开头：用 emoji 或简短文字吸引注意 📸
中间：详细内容，分点列举，使用空行分段
结尾：引导互动 - 点赞👍 收藏⭐ 关注💕
```

**图片要求：**
- 使用本地绝对路径更稳定
- 多图时注意排版和顺序
- 确保图片清晰、美观

**视频要求：**
- 文件大小 < 1GB
- 使用常见格式（MP4、MOV）
- 时长建议 15 秒 - 5 分钟

### 常见问题

**Q: 提示"找不到 MCP 工具"？**

A: 检查以下几点：
1. MCP 服务是否启动：访问 `http://localhost:18060/mcp`
2. 是否已添加到 Claude Code：`claude mcp list`
3. 如未添加，执行：`claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp`

**Q: 发布失败，提示"未登录"？**

A: 在 Claude Code 中说"登录小红书"：
1. Claude 会获取二维码并保存为 `xiaohongshu_login_qrcode.png`
2. 打开图片，用小红书 App 扫码登录
3. 扫码后告诉 Claude "已登录"

**Q: 二维码过期了？**

A: 二维码有效期约 5 分钟，告诉 Claude "重新获取二维码" 即可。

**Q: 标题或内容太长怎么办？**

A: Claude 会自动检测并提示你精简：
- 标题限制：20 个字符
- 内容限制：1000 个字符

**Q: 图片路径错误？**

A: 确保使用绝对路径，例如：
- ✅ `/Users/liuyishou/Pictures/photo.jpg`
- ❌ `~/Pictures/photo.jpg`
- ❌ `photo.jpg`

**Q: 视频上传失败？**

A: 检查：
1. 视频文件是否存在
2. 是否使用绝对路径
3. 文件大小是否 < 1GB
4. 格式是否为常见视频格式

**Q: MCP 服务如何后台运行？**

A: 使用 `nohup` 或 `screen` 在后台运行：

```bash
# 使用 nohup
nohup go run . &

# 或使用 screen
screen -S xiaohongshu-mcp
go run .
# 按 Ctrl+A, D 分离会话
```

## 应用场景

### ✅ 推荐使用

- **内容营销** - 快速发布产品推广内容
- **生活分享** - 记录日常生活、旅行、美食
- **教程分享** - 发布技能教程、经验分享
- **品牌运营** - 批量管理小红书账号内容
- **自动化发布** - 结合其他工具实现定时发布

### 📝 使用示例

**场景 1: 旅行博主**
```
帮我发布三亚旅行日记：
标题：三亚5日游攻略
内容：Day1-Day5 的详细行程，包含酒店推荐、景点介绍、美食推荐...
图片：[旅行照片路径列表]
```

**场景 2: 美食博主**
```
发布今天的美食视频：
标题：提拉米苏教程
内容：详细步骤和注意事项
视频：/Users/xxx/Videos/tiramisu.mp4
```

**场景 3: 穿搭博主**
```
分享今日穿搭：
标题：通勤穿搭｜简约风
内容：衣服品牌、搭配思路、适合场合
图片：穿搭照片
```

## 技术架构

### 组件关系

```
┌─────────────────┐
│   用户请求      │ "帮我发小红书笔记"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claude Code    │ 读取 SKILL.md，理解发布流程
│  + Skill        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MCP 工具调用   │ xiaohongshu_publish_content
│                 │ xiaohongshu_publish_with_video
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 小红书 MCP 服务 │ http://localhost:18060/mcp
│  (Go 服务)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  小红书平台     │ 内容发布成功
└─────────────────┘
```

### MCP 工具说明

Skill 使用以下 MCP 工具（由小红书 MCP 服务提供）：

**登录相关：**
1. **check_login_status** - 检查当前登录状态
2. **get_login_qrcode** - 获取登录二维码（返回 Base64 图片）
3. **delete_cookies** - 删除登录信息，用于切换账号

**发布相关：**
4. **publish_content** - 发布图文内容（参数：title, content, tags, images）
5. **publish_with_video** - 发布视频内容（参数：title, content, tags, video）

**注意：** `tags` 参数是数组格式，如 `["美食", "旅行"]`，不要在内容中使用 `#标签` 格式

**其他功能：**
6. **list_feeds** - 获取首页 Feeds 列表
7. **search_feeds** - 搜索小红书内容
8. **get_feed_detail** - 获取笔记详情
9. **like_feed** - 点赞/取消点赞
10. **favorite_feed** - 收藏/取消收藏
11. **post_comment_to_feed** - 发表评论
12. **user_profile** - 获取用户主页信息

这些工具在 Claude Code 中会自动可用（前提是已添加 MCP 服务）。

## 故障排查

### MCP 服务问题

**服务无法启动：**
1. 检查 Go 环境是否安装：`go version`
2. 检查端口 18060 是否被占用：`lsof -i :18060`
3. 查看项目 README 的故障排查部分

**服务运行但无法连接：**
1. 确认服务地址：`http://localhost:18060/mcp`
2. 测试连接：`curl http://localhost:18060/mcp`
3. 检查防火墙设置

### 发布问题

**发布失败：**
1. 检查是否已登录
2. 验证参数是否符合要求
3. 查看 MCP 服务日志
4. 使用 `-headless=false` 模式观察浏览器操作

**图片/视频上传失败：**
1. 确认文件存在
2. 检查文件权限
3. 验证路径格式（必须是绝对路径）
4. 视频文件大小是否 < 1GB

### 调试技巧

**启用浏览器界面：**
```bash
go run . -headless=false
```

可以看到 MCP 服务在浏览器中的实际操作，便于调试。

**查看 MCP 工具列表：**
```bash
# 在 Claude Code 中
列出所有可用的 MCP 工具
```

Claude 会列出所有已连接的 MCP 服务及其提供的工具。

## 安全与隐私

### 数据安全

- ✅ 登录信息存储在本地
- ✅ 不会上传到第三方服务器
- ✅ MCP 服务仅在本地运行（127.0.0.1）
- ⚠️ 建议使用小号进行测试

### 内容合规

- 发布内容需遵守小红书社区规范
- 避免违规内容（虚假广告、引流、敏感信息等）
- 建议先在小红书 APP 中测试发布流程

### 账号安全

- 不要在公共电脑上登录
- 定期检查账号安全设置
- 如发现异常，立即修改密码

## 进阶使用

### 批量发布

```
我有 10 篇内容要发布到小红书，内容在 /path/to/contents.json
帮我批量发布
```

Claude 会读取文件，逐条发布。

### 定时发布

可以结合 cron 或其他定时任务工具实现：

```bash
# crontab 示例
0 9 * * * echo "发布今日内容" | claude
```

### 内容模板

可以创建内容模板文件，快速生成发布内容：

```json
{
  "title": "每日穿搭",
  "content_template": "今日穿搭：{outfit}\n品牌：{brand}\n搭配建议：{tips}",
  "images": []
}
```

## 相关资源

- **小红书 MCP 项目**: https://github.com/xpzouying/xiaohongshu-mcp
- **MCP 协议文档**: https://modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Claude Code 文档**: https://code.claude.com/docs

## 贡献与反馈

发现问题或有改进建议？

1. 提交 Issue
2. 提交 Pull Request
3. 分享你的使用案例

## 许可证

MIT License - 自由使用和修改

---

**开始使用：**

1. 启动小红书 MCP 服务：`go run .`
2. 添加到 Claude Code：`claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp`
3. 安装 skill：`cp -r xiaohongshu ~/.claude/skills/`
4. 在 Claude Code 中说："登录小红书"
5. 开始发布："帮我发一篇小红书笔记"

🚀 享受便捷的小红书内容发布体验！

---
name: social-media-publish
description: "统一社交媒体发布工具 - 支持 X (Twitter)、小红书、B站。一次创作，多平台分发。"
allowed-tools: "*"
---

# 社交媒体统一发布工具

一站式发布内容到 X (Twitter)、小红书、B站三大平台。

## 触发条件

用户提到以下关键词时触发：
- "发社交媒体"、"多平台发布"、"一键发布"
- "发推"、"发twitter"、"发x" → X平台
- "发小红书"、"发xhs" → 小红书
- "发b站"、"发bilibili"、"投稿b站" → B站

## 平台能力对照

| 平台 | 内容类型 | 限制 | 登录方式 |
|------|----------|------|----------|
| **X (Twitter)** | 文字+图片 | 280字符，4张图 | API密钥（已配置） |
| **小红书** | 图文/视频 | 标题20字，正文1000字 | 扫码登录 |
| **B站** | 视频 | 标题80字，需视频文件 | 扫码登录 |

## 快速开始

### 单平台发布

```
发到X: 今天天气真好！
发小红书: [标题] [正文] [图片路径]
发B站: [视频路径] [标题]
```

### 多平台同步

```
帮我把这段内容发到X和小红书：
[你的内容]
```

---

## 一、X (Twitter) 发布

### 1.1 基本用法

```bash
python3 ~/.claude/skills/x-post/scripts/x_post.py "推文内容" [OPTIONS]
```

### 1.2 参数说明

| 参数 | 说明 |
|------|------|
| `text` | 推文内容（必填，最多280字符） |
| `--images` / `-i` | 图片路径（最多4张） |

### 1.3 示例

**纯文本推文：**
```bash
python3 ~/.claude/skills/x-post/scripts/x_post.py "今天天气真好！"
```

**带图片推文：**
```bash
python3 ~/.claude/skills/x-post/scripts/x_post.py "看看这张照片" -i /path/to/image.jpg
```

### 1.4 注意事项

- 推文限制 280 字符
- 图片支持 JPG、PNG、GIF
- API 限制：每 15 分钟最多 100 条
- 账号：liuysh2

---

## 二、小红书发布

### 2.1 登录检查（必须先执行）

```bash
# 检查登录状态
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py check

# 未登录则获取二维码
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py qrcode
```

### 2.2 发布图文

```bash
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py publish \
  --title "标题（≤20字）" \
  --content "正文内容（≤1000字，不含#标签）" \
  --tags "标签1,标签2,标签3" \
  --images "/path/to/image.jpg"
```

### 2.3 发布视频

```bash
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py video \
  --title "标题" \
  --content "正文内容" \
  --tags "标签1,标签2" \
  --video "/path/to/video.mp4"
```

### 2.4 或使用 MCP 工具

如果 MCP 服务已启动，可直接调用：
- `check_login_status` - 检查登录
- `get_login_qrcode` - 获取二维码
- `publish_content` - 发布图文
- `publish_with_video` - 发布视频

### 2.5 限制说明

- 标题：≤20 字符
- 正文：≤1000 字符（不要在正文里写 #标签）
- 标签：数组格式，不带 # 符号
- 图片：本地绝对路径（推荐）或 URL
- 视频：仅支持本地绝对路径，建议 <1GB

---

## 三、B站发布

### 3.1 登录检查

```bash
# 检查 cookies 是否存在
ls ~/.claude/skills/biliup-publish/cookies.json

# 如需登录
cd ~/.claude/skills/biliup-publish && biliup login
```

### 3.2 上传视频

```bash
cd ~/.claude/skills/biliup-publish
biliup upload "/path/to/video.mp4" \
  --title "视频标题（≤80字）" \
  --desc "视频简介" \
  --tag "标签1,标签2" \
  --tid 231 \
  --copyright 1
```

### 3.3 常用分区 ID

| tid | 分区 | 适用内容 |
|-----|------|----------|
| 231 | 计算机技术 | 编程、AI、技术教程 |
| 230 | 软件应用 | 软件测评、使用教程 |
| 201 | 科学科普 | 知识科普 |
| 207 | 财经商业 | 商业、投资 |
| 160 | 生活记录 | 日常Vlog |
| 138 | 搞笑 | 搞笑内容 |

### 3.4 注意事项

- 标题：≤80 字符
- 标签：≤12 个，每个≤20字
- 封面：建议 1920x1080 或 1280x720
- copyright：1=自制，2=转载
- 账号：转了码的刘公子

---

## 四、多平台发布工作流

当用户要求多平台发布时，按以下流程执行：

### Step 1: 确认内容和目标平台

询问用户：
1. 发布内容是什么？（文字/图片/视频）
2. 发布到哪些平台？

### Step 2: 检查登录状态

对每个目标平台检查登录状态：

```bash
# X - 无需检查，API密钥已配置

# 小红书
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py check

# B站
ls ~/.claude/skills/biliup-publish/cookies.json
```

### Step 3: 内容适配

根据平台限制自动调整内容：

| 平台 | 文字处理 | 媒体处理 |
|------|----------|----------|
| X | 精简到280字以内 | 最多4张图 |
| 小红书 | 标题≤20字，正文≤1000字 | 图片/视频 |
| B站 | 标题≤80字 | 仅视频 |

### Step 4: 依次发布

按顺序发布到各平台，每个平台完成后汇报结果。

### Step 5: 汇总结果

```
发布结果：
✅ X: https://x.com/i/status/xxx
✅ 小红书: 发布成功
✅ B站: https://www.bilibili.com/video/BVxxx
```

---

## 五、内容创作辅助

### 5.1 爆款标题公式

**小红书/B站标题模板：**
```
数字+结果：「3招搞定xxx，效果绝了！」
身份+痛点：「打工人必看！xxx的正确姿势」
反常识+好奇：「原来xxx才是关键，后悔没早知道」
```

**X 推文精简技巧：**
- 保留核心观点
- 删除详细解释
- 善用 emoji 增强表现力

### 5.2 标签生成

从内容中提取 3-6 个关键词：
- 核心主题词（1-2个）
- 人群词（打工人、学生党）
- 场景词（日常、通勤）

### 5.3 封面生成（小红书）

使用 nanobanana-draw 生成文字封面：

```
生成一张小红书风格封面图，3:4竖版比例，
纯白色背景，中间用黑色大字写着：[主标题]，
下面小字写：[副标题]，
字体简洁现代，排版居中，极简风格
```

---

## 六、故障排查

### X 发布失败

1. 检查内容是否超过 280 字符
2. 检查图片格式和大小
3. API 调用频率限制（15分钟100条）

### 小红书发布失败

1. 检查登录状态：`python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py check`
2. 标题/正文是否超长
3. 文件路径是否为绝对路径
4. MCP 服务是否运行

### B站发布失败

1. 检查 cookies：`ls ~/.claude/skills/biliup-publish/cookies.json`
2. 刷新登录：`cd ~/.claude/skills/biliup-publish && biliup renew`
3. 视频格式是否支持
4. 分区 ID 是否正确

---

## 七、平台特性速查

| 特性 | X | 小红书 | B站 |
|------|---|--------|-----|
| 文字限制 | 280字符 | 1000字符 | 视频简介无硬性限制 |
| 图片 | ✅ 最多4张 | ✅ | ❌ 仅封面 |
| 视频 | ❌ | ✅ | ✅ |
| 标签 | 可用#号 | 数组格式 | 逗号分隔 |
| API方式 | REST API | MCP/脚本 | CLI工具 |
| 登录 | API密钥 | 扫码 | 扫码 |

---

## 八、一键多平台示例

**场景：发布一条知识分享**

用户说："帮我把这段内容发到X和小红书"

执行步骤：

1. **X 版本（精简版）：**
```bash
python3 ~/.claude/skills/x-post/scripts/x_post.py "核心观点精简版（280字内）" -i 封面图.jpg
```

2. **小红书版本（完整版）：**
```bash
python3 ~/.claude/skills/xiaohongshu/scripts/xhs_publish.py publish \
  --title "吸引眼球的标题" \
  --content "完整正文内容..." \
  --tags "标签1,标签2,标签3" \
  --images 封面图.jpg
```

3. **汇总反馈：**
```
✅ 已发布到 2 个平台：
- X: https://x.com/i/status/xxx
- 小红书: 发布成功
```

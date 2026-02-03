# B站视频发布 (biliup-publish)

通过 biliup CLI 工具将视频上传并发布到 Bilibili。

## 触发条件

用户说"发b站"、"上传b站"、"投稿b站"、"发bilibili"等。

## 前置条件

- biliup CLI 已安装（`biliup --version` 验证）
- 已登录（cookies 文件存在）

## 工作流（必须遵循）

### Step 1: 确认登录状态

检查 cookies 文件是否存在：

```bash
ls -la /Users/liuyishou/.claude/skills/biliup-publish/cookies.json 2>/dev/null
```

如果不存在，提示用户需要先登录：

```bash
cd /Users/liuyishou/.claude/skills/biliup-publish
biliup login
```

登录会弹出二维码，用户用 B站App 扫码完成登录。cookies 保存在当前目录的 `cookies.json`。

### Step 2: 确认视频文件

与用户确认：
- 视频文件路径（必须是本地文件）
- 如果用户没给文件路径，问用户

支持格式：mp4, flv, mkv, avi 等主流格式。

### Step 3: 确认发布信息

与用户确认以下信息（有默认值的可不问）：

| 参数 | 说明 | 是否必填 |
|------|------|----------|
| title | 视频标题 | 必填 |
| desc | 视频简介 | 选填（默认空） |
| tag | 标签，逗号分隔 | 选填 |
| tid | 分区ID | 选填（默认171-电子竞技） |
| cover | 封面图片路径 | 选填（B站会自动截取） |
| copyright | 1=自制 2=转载 | 选填（默认1） |
| source | 转载来源URL | 转载时必填 |

### Step 4: 执行上传

```bash
cd /Users/liuyishou/.claude/skills/biliup-publish
biliup upload "视频文件路径" \
  --title "标题" \
  --desc "简介" \
  --tag "标签1,标签2" \
  --tid 分区ID \
  --cover "封面路径" \
  --copyright 1
```

### Step 5: 确认结果

上传成功后会返回视频 BV 号，告知用户视频链接：
`https://www.bilibili.com/video/BVxxxxxxxx`

## 常用分区 ID (tid)

### 知识区
| tid | 分区名 |
|-----|--------|
| 201 | 科学科普 |
| 207 | 财经商业 |
| 209 | 职业职场 |
| 228 | 人文历史 |
| 122 | 野生技术协会（已合并到科技） |

### 科技区
| tid | 分区名 |
|-----|--------|
| 95  | 数码 |
| 230 | 软件应用 |
| 231 | 计算机技术 |
| 232 | 科技人文 |
| 233 | 极客DIY |

### 生活区
| tid | 分区名 |
|-----|--------|
| 138 | 搞笑 |
| 160 | 生活记录 |
| 161 | 美食圈 |
| 162 | 宠物 |
| 163 | 运动 |
| 176 | 汽车 |
| 250 | 出行 |
| 251 | 三农 |
| 239 | 家居房产 |

### 娱乐区
| tid | 分区名 |
|-----|--------|
| 71  | 综艺 |
| 137 | 明星八卦 |
| 241 | 娱乐杂谈 |

### 影视区
| tid | 分区名 |
|-----|--------|
| 182 | 影视杂谈 |
| 183 | 影视剪辑 |
| 184 | 短片 |
| 85  | 小剧场 |

### 动画/游戏
| tid | 分区名 |
|-----|--------|
| 27  | 综合动画 |
| 171 | 电子竞技 |
| 172 | 手机游戏 |
| 173 | 单机游戏 |

### 音乐区
| tid | 分区名 |
|-----|--------|
| 28  | 原创音乐 |
| 31  | 翻唱 |
| 59  | 演奏 |
| 193 | MV |
| 29  | 音乐现场 |

### 教育区
| tid | 分区名 |
|-----|--------|
| 211 | 校园学习 |
| 124 | 社科·法律·心理 |
| 213 | 语言学习 |
| 210 | 职业考试 |

## 高级用法

### 多P投稿（追加视频）

```bash
biliup append --vid BVxxxxxxxx "追加的视频.mp4" \
  -u /Users/liuyishou/.claude/skills/biliup-publish/cookies.json
```

### 定时发布

```bash
# dtime 为10位时间戳，距提交需大于4小时
biliup upload "video.mp4" --title "标题" --dtime 1706140800
```

### 仅自己可见（草稿）

```bash
biliup upload "video.mp4" --title "标题" --is-only-self 1
```

### 刷新登录

```bash
cd /Users/liuyishou/.claude/skills/biliup-publish
biliup renew
```

## 注意事项

1. cookies 文件路径固定在 skill 目录：`/Users/liuyishou/.claude/skills/biliup-publish/cookies.json`
2. 所有 biliup 命令都需要 `-u` 指定 cookies 路径（或在 skill 目录下执行）
3. 上传大文件可能耗时较长，使用 `--limit` 控制并发数
4. 封面图片建议尺寸 1920x1080 或 1280x720
5. 标签总数不超过12个，单个标签不超过20字
6. 标题最长80字符

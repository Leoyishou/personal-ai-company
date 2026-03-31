---
name: ima-downloader
description: "下载 IMA Copilot 知识库中的所有文件到本地。支持 PDF、Word 等文件下载，以及笔记摘要导出为 Markdown。"
---

# IMA 知识库下载器

下载 IMA Copilot 知识库中的所有文件到本地。

## When to Use

当用户想要下载 IMA Copilot 知识库内容时使用：

- "/ima-downloader 一人公司"
- "帮我下载这个 IMA 知识库"
- "把 IMA 知识库的文件保存到本地"

## 前置条件

需要 Cookie 文件 `/tmp/ima_cookie.txt` 和知识库 ID。

### 一键获取 Cookie 和 ID

提供这个命令让用户运行：

```bash
mitmdump --mode local:ima-copilot -p 8888 -s ~/.claude/skills/ima-downloader/scripts/capture.py
```

然后告诉用户：
> 1. 命令已启动代理
> 2. 现在打开 IMA 应用，进入"一人公司"知识库
> 3. 终端会自动显示知识库 ID
> 4. 把显示的 ID 告诉我

这个脚本会自动：
- 保存 Cookie 到 `/tmp/ima_cookie.txt`
- 显示捕获到的知识库 ID

## Workflow

### Step 1: 检查 Cookie

```bash
test -f /tmp/ima_cookie.txt && echo "Cookie 存在" || echo "需要配置 Cookie"
```

### Step 2: 获取分享链接

**重要**: 用户可能不知道知识库 ID，需要引导他们获取分享链接。

告诉用户:
> 请在 IMA 应用中：
> 1. 打开"一人公司"知识库
> 2. 点击右上角「分享」按钮
> 3. 复制分享链接给我

分享链接格式类似: `https://ima.qq.com/share?knowledgeId=7383025226642484&...`

### Step 3: 冒烟测试

收到分享链接后，运行冒烟测试：

```bash
python3 /Users/liuyishou/.claude/skills/ima-downloader/scripts/ima_downloader.py "<分享链接>" --smoke-test
```

脚本会自动从链接中提取知识库 ID。

如果出现 `code: 600001` 错误，提示用户 Cookie 已过期需要刷新。

### Step 4: 确认下载

使用 AskUserQuestion 显示冒烟测试结果，询问是否继续：
- 总文件数
- 可下载文件数
- 笔记数量
- 预计大小

### Step 5: 执行下载

```bash
python3 /Users/liuyishou/.claude/skills/ima-downloader/scripts/ima_downloader.py "<分享链接>" --download-all
```

### Step 6: 报告结果

- 下载的文件数
- 导出的笔记数
- 保存位置: `~/Downloads/IMA_知识库/<知识库名称>/`
- 总大小

## Usage Examples

```bash
# 使用分享链接 (推荐)
python3 .../ima_downloader.py "https://ima.qq.com/share?knowledgeId=7383025226642484"

# 使用纯 ID
python3 .../ima_downloader.py 7383025226642484

# 冒烟测试
python3 .../ima_downloader.py "<链接或ID>" --smoke-test

# 完整下载
python3 .../ima_downloader.py "<链接或ID>" --download-all
```

## Output Structure

```
~/Downloads/IMA_知识库/<知识库名称>/
├── files/              # PDF, Word 等文件
├── notes_摘要版/       # Markdown 笔记摘要
└── file_list.json     # 完整文件索引
```

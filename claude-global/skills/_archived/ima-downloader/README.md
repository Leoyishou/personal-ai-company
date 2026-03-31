# IMA Copilot 知识库下载器

下载 IMA Copilot (腾讯 AI 知识库应用) 中的知识库内容到本地。

## 功能

- 批量下载 PDF、Word、PPT 等文件
- 导出笔记摘要为 Markdown
- 保留目录结构
- 冒烟测试验证

## 快速开始

```bash
# 1. 获取 Cookie (使用 mitmproxy)
mitmproxy --mode local:ima-copilot -p 8888
# 打开 IMA，复制 Cookie 到 /tmp/ima_cookie.txt

# 2. 冒烟测试
python3 scripts/ima_downloader.py --id "知识库ID" --smoke-test

# 3. 完整下载
python3 scripts/ima_downloader.py --id "知识库ID" --download-all
```

## 技术原理

1. 使用 `get_knowledge_list` API 获取文件列表
2. 使用 `get_knowledge` API 获取签名下载 URL
3. 通过签名 URL 绕过腾讯云 COS 403 限制
4. 笔记使用 `introduction` + `abstract` 字段导出摘要

## 已知限制

- Cookie 有效期约 24 小时
- 笔记仅能导出摘要，完整内容需在 IMA 查看

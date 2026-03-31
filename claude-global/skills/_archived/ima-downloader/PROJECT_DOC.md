# IMA 知识库下载器 - 项目文档

## 项目概述

**目标**: 将 IMA Copilot 知识库内容批量下载到本地，封装为可复用的 Claude Code skill。

**成果**:
- 下载 566 个文件 (1.2 GB)
- 导出 485 篇笔记摘要
- 可复用 `/ima-downloader` skill

---

## 核心动作流

```
问题发现 → API逆向 → 文件下载 → 笔记导出 → 技能封装
   ↓          ↓          ↓          ↓          ↓
403错误   mitmproxy   签名URL    摘要提取   Claude Code skill
```

---

## 关键节点与效果

| 节点 | 技术难点 | 解决方案 | 效果 |
|------|---------|---------|------|
| API 逆向 | CDN 403 Forbidden | mitmproxy 抓包，发现 `get_knowledge` 返回签名 URL | 突破下载限制 |
| 文件下载 | 目录结构、批量处理 | 递归遍历 + 签名 URL | 566 文件 / 1.2 GB |
| 笔记导出 | 笔记无法直接下载 | `introduction` + `abstract` 字段 | 485 篇 Markdown |
| 技能封装 | Cookie 过期 | 清晰错误提示 + 刷新指南 | 可复用 skill |

---

## 技术关键词

| 类别 | 关键词 |
|------|--------|
| 网络抓包 | mitmproxy, HTTPS 拦截, Cookie |
| API 逆向 | REST API, 签名 URL, x-ima-bkn (CSRF) |
| 云存储 | 腾讯云 COS, x-cos-security-token |
| 工程化 | Claude Code Skill, 冒烟测试 |

---

## 核心 API

| API | 用途 |
|-----|------|
| `get_knowledge_list` | 获取文件列表 |
| `get_knowledge` | 获取签名 URL + 笔记摘要 |

---

## 签名 URL 机制

```
原始 URL: ima-share-kb.image.myqcloud.com/xxx.pdf → 403
签名 URL: ...?sign=xxx&x-cos-security-token=xxx  → 200
```

---

## 文件结构

```
~/.claude/skills/ima-downloader/
├── SKILL.md           # Skill 定义
├── README.md          # 使用说明
├── PROJECT_DOC.md     # 项目文档
└── scripts/
    └── ima_downloader.py  # 核心脚本
```

---

## 效果统计 (Dan Koe 知识库)

| 指标 | 数值 |
|------|------|
| 总文件数 | 1054 |
| 下载文件 | 566 个 |
| 下载大小 | 1.2 GB |
| 笔记导出 | 485 篇 |
| 成功率 | 100% |

---

*文档生成: 2026-01-11*

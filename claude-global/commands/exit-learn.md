# /exit-learn - Session 知识萃取 → Obsidian 图文学习笔记

回顾本次完整 session，将其中对用户而言的「新知识」提炼为图文并茂的 Obsidian 学习笔记。

---

## Step 1: 提取 Session 知识清单

分析整个对话历史，识别所有出现过的知识点：

- **概念**：新术语、技术名词、设计模式
- **工具/库**：使用的框架、API、CLI 工具
- **技巧/原理**：解决问题的思路、底层机制、最佳实践
- **流程/架构**：系统设计方案、工作流

每个知识点用一行列出：`名称 | 类型 | 一句话描述 | 所属领域`

---

## Step 2: 知识缺口分析（找出「新知」）

对 Step 1 中每个知识点，在 Obsidian 中检查是否已有笔记：

```bash
# 方法1：按文件名查找
ls /Users/liuyishou/usr/odyssey/2\ 第二大脑/1\ 概念/ -R 2>/dev/null | grep -i "关键词"

# 方法2：搜索文件内容
grep -r "关键词" /Users/liuyishou/usr/odyssey/ --include="*.md" -l 2>/dev/null | head -3
```

分类结果：
- ✅ **已知**：Obsidian 中已有笔记 → 跳过
- 🆕 **新知**：Obsidian 中无相关笔记 → 纳入本次学习笔记

**控制规模：最多保留 5 个最有价值的新知识点。**
优先级：原理 > 概念 > 工具 > 技巧

---

## Step 3: 确定保存路径

笔记统一保存到 Obsidian 收集箱：

- **笔记**：`/Users/liuyishou/usr/odyssey/0 收集箱/YYYYMMDD-[session主题].md`
- **图片**：`/Users/liuyishou/usr/odyssey/0 收集箱/assets/`

---

## Step 4: 为每个新知识点生成图解

对 Step 2 中筛选出的每个新知识点，生成手绘白板图：

### 4.1 整理图解内容

| 问题 | 技术回答（关键词） | 小白秒懂版（类比/口诀） |
|------|------------------|----------------------|
| [知识点核心问题] | [技术要点，3-5 个] | [通俗类比或场景] |

### 4.2 生成手绘白板图

```bash
# SAVE_DIR = 笔记目录/assets/
cd ~/.claude/skills/api-draw
python scripts/nanobanana_draw.py "Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art,
bold black marker strokes with blue highlight accents,
pure white background, clean and professional.

Title: 「[知识点名称]」in bold hand-drawn style with blue underline.

Section 1 - What is it? (核心定义):
- [要点1] with simple icon
- [要点2] with simple icon

Section 2 - How it works? (工作原理):
- [步骤/机制] with arrows/flow

Section 3 - Key insight (核心洞见):
- [口诀或记忆点] in highlighted box

Excalidraw hand-drawn aesthetic, Chinese text primarily, NOT cute/kawaii." \
  --style "手绘白板" \
  --subject "[知识点名称]" \
  --save-dir "[笔记目录]/assets/"
```

**规则：**
- 每个知识点生成 1 张图（内容丰富时拆成 2 张后水平拼接）
- 图名：`知识点名称_手绘白板_0.png`（api-draw 自动生成）

---

## Step 5: 组装 Markdown 学习笔记

笔记文件名：`YYYYMMDD-[session主题].md`（例：`20260220-Claude-Hooks机制.md`）

```markdown
---
date: YYYY-MM-DD
session: "[session简述]"
tags: [领域标签]
source: session
---

# [Session 主题] 学习笔记

> **Session 背景**：[一句话描述这次 session 做了什么]
> **新知识点**：N 个

---

## 一、[知识点名称]

**是什么**：[一句话定义]

**核心机制**：

| 问题 | 技术回答 | 小白秒懂版 |
|------|----------|-----------|
| [问题] | [技术要点] | [通俗类比] |

**口诀**：[一句话记忆口诀]

![[assets/知识点名称_手绘白板_0.png]]

**与已知的关联**：[连接到用户已有知识体系中的哪个点]

---

## 二、[知识点名称]

[同上格式]

---

## 总结

| 知识点 | 核心要点 | 记忆口诀 | 所属领域 |
|--------|----------|----------|---------|
| [名称] | [要点] | [口诀] | [领域] |

**本次 session 最大收获**：[1-2 句话]
```

---

## Step 6: 保存并汇报

1. 将笔记文件写入确定的 Obsidian 路径
2. 输出完成汇报：

```
## 📚 Session 知识萃取完成

**本次 Session**：[简述]
**扫描知识点**：N 个
**已在 Obsidian**：X 个（跳过）
**新增学习笔记**：Y 个概念

**笔记已保存**：
📄 [文件名](完整路径)

**新知识点**：
- [概念1]：[一句话]
- [概念2]：[一句话]
```

---

## 注意事项

- **不要生成用户深度领域（deep）的入门级知识**，如「Python 什么是函数」这种——用户早就知道了
- **聚焦 session 中真正新出现的内容**：新 API、新机制、新架构模式、新工具
- **图文要配套**：有图才算图文并茂，不要因为「太简单」跳过图片生成
- **与已知关联**：每个知识点都要写「与已知的关联」，帮助用户内化到已有体系
- 笔记风格：**结构清晰 > 内容完整**，宁少勿滥

---
name: explain
description: 通俗解释 + 图解 - 将复杂概念用大白话讲清楚，自动选择风格并生成可视化图。
allowed-tools: Bash(python:*), Read, Write
model: sonnet
tags: [explain, visual, education]
user-invocable: true
invocation:
  - /explain
  - /解释
  - /通俗
  - /图解
triggers:
  - 通俗解释
  - 解释一下
  - 什么是
  - 讲讲
  - 说说
  - 科普一下
  - 给我讲讲
  - 图解
  - 画个图解释
  - 形象说明
  - 帮我可视化
  - 用图说明
  - 画出来讲
---

# 通俗解释 + 图解

将复杂概念转化为通俗易懂的图解，自动选择最佳风格。

## 工作流（必须严格遵循）

### Step 0: 判断入口

**根据用户输入决定从哪一步开始：**

| 用户输入 | 起始步骤 |
|----------|----------|
| 只有问题，无表格 | 从 Step 1 开始（整理表格） |
| 已提供三列表格 | 跳过 Step 1，直接 Step 2（判断风格）→ Step 3（画图） |
| 问题 + 类比提示 | 调用 Gemini 生成解释 → Step 3（画图） |

### Step 1: 整理三列表格（用户未提供时）

**先输出结构化表格，等用户确认后再画图。**

| 问题 | 技术回答（关键词） | 小白秒懂版（类比/故事） |
|------|-------------------|----------------------|
| 问题1 | 技术要点 | 通俗比喻 |

**表格要求：**
- 第一列：问题本身
- 第二列：技术回答（关键词、要点）
- 第三列：小白秒懂版（类比、故事化）

**附加：一句话记忆口诀表**

| 概念 | 口诀 |
|------|------|
| 概念1 | 精炼记忆点 |

**或调用 Gemini 生成：**

```bash
cd ~/.claude/skills/通俗解释
python scripts/explain_concept.py "[概念]" --hint "[可选类比提示]"
```

### Step 2: 判断风格 & 图片数量

#### 2.1 风格选择

**唯一风格：手绘白板**（适用于所有场景）

> **IMPORTANT**: 禁止使用小红书卡片/kawaii/可爱风格，那种粉嫩、爱心、星星、大眼睛卡通人物的风格用于技术概念太腻太丑。

| 内容类型 | 推荐风格 | 适用场景 |
|----------|----------|----------|
| **技术概念**（CS、编程、架构、并发） | 手绘白板 | DevOps、锁升级、微服务、DDD 等 |
| **流程/阶段**（多步骤演进） | 手绘白板 + 多图拼接 | synchronized 锁升级、TCP 握手等 |
| **对比类**（A vs B） | 手绘白板对比布局 | 贫血vs充血、同步vs异步等 |
| **生活场景类比** | 手绘白板 | 快递、餐厅、钓鱼等类比也用手绘白板 |

**关键原则：无论什么内容，一律使用手绘白板风格。简洁、专业、清晰。**

#### 2.2 内容量判断 → 图片数量

| 内容类型 | 图片策略 |
|----------|----------|
| 1-3 个要点的单一概念 | 1 张图 |
| 4-6 个要点或 2-3 个阶段 | 2 张图，虚线框拼接 |
| 7+ 个要点或 4+ 个阶段 | 先拆分，后拼接成合集 |
| 多个独立问题（批量处理） | 每个问题 1 张图，不拼接 |

**多阶段流程拆分示例（如 synchronized 锁升级）：**
- 4 个阶段 → 拆成 2 张图（每张 2 阶段）→ 水平拼接
- 6 个阶段 → 拆成 3 张图（每张 2 阶段）→ 水平拼接
- 每张图内用「左右分栏」展示相邻阶段

### Step 3: 生成图片

#### 3.1 手绘白板风格（唯一风格）

```bash
cd ~/.claude/skills/api-draw
python scripts/nanobanana_draw.py "Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art,
bold black marker strokes with blue highlight accents,
pure white background, clean and professional.

Title: 「[中文标题]」in bold hand-drawn style with blue underline.

Content (key points with simple doodle icons):
- [要点1] with [图标]
- [要点2] with [图标]

Summary box at bottom.
Excalidraw hand-drawn aesthetic, simple doodle." \
  --style "手绘白板" \
  --subject "[主题名]"
```

### Step 4: 多图拼接（内容量大时）

当一个问题需要多张图时，使用虚线边框拼接成合集：

```bash
cd ~/.claude/skills/api-draw
python scripts/image_stitch.py \
  图1.jpg 图2.jpg 图3.jpg \
  -o [主题]_合集.jpg \
  -d horizontal \
  --border-style dashed \
  -g 30 -p 40
```

**拼接规则：**
- 2 张图 → 水平拼接 1×2
- 3 张图 → 水平拼接 1×3
- 4 张图 → 2×2 网格（先水平拼两行，再垂直合并）
- 6 张图 → 2×3 网格

### Step 5: 输出 MD 文档

生成 Markdown 文档，包含问题详解 + 图片 + 总结表。

---

## 风格 Prompt 模板库

> **禁止使用的风格**：小红书卡片 / kawaii / 可爱风 / 粉嫩色系 / 大眼睛卡通 / LINE sticker 风格。这些风格用于技术图解太腻太丑。

### 手绘白板风格（唯一风格）

```
Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art,
bold black marker strokes with blue highlight accents,
pure white background, clean and professional.

Title: 「[标题]」in bold hand-drawn style with blue underline.

Content with simple doodle icons:
- [要点] with stick figures/simple shapes
- Arrows connecting concepts

Summary box: [口诀]
Excalidraw aesthetic, childlike sketch, NOT realistic.
Chinese text primarily.
```

### 对比风格

```
Split comparison illustration, 3:4 vertical ratio,
LEFT side vs RIGHT side layout,
clear visual contrast between two concepts,
hand-drawn style with color coding (blue vs orange/red).

Title: 「[A] vs [B]」

LEFT - [概念A]:
- [特点1] with icon
- [特点2] with icon

RIGHT - [概念B]:
- [特点1] with icon
- [特点2] with icon

Bottom: comparison summary table or key differences.
Chinese text, clear separation line in middle.
```

---

## 图标映射表

| 概念类型 | 推荐图标 |
|----------|----------|
| 开始/输入 | arrow, door, power button |
| 检查/验证 | magnifying glass, checklist, shield |
| 处理/转换 | gear, brain, lightning bolt |
| 存储/记忆 | database, folder, box |
| 输出/结果 | screen, document, trophy |
| 用户/人 | stick figure, cute cartoon character |
| 网络/连接 | globe, wifi symbol, arrows |
| 时间/顺序 | clock, numbered steps, timeline |
| 安全/加密 | lock, key, shield |
| 快递/传输 | package, truck, delivery person |
| 餐厅/服务 | waiter, chef, menu |
| 家庭/关系 | house, family members |

---

## 自动风格选择规则

**唯一规则：所有内容 → 手绘白板**

| 内容主题 | 风格 | 说明 |
|----------|------|------|
| CS/编程/架构/并发 | 手绘白板 | DevOps、微服务、锁、线程池等 |
| 网络/协议 | 手绘白板 | TCP、HTTP、DNS、CORS 等 |
| 数据结构/算法 | 手绘白板 | 队列、栈、树、图等 |
| 设计模式/DDD | 手绘白板 | 工厂、观察者、聚合根等 |
| 对比类（A vs B） | 手绘白板对比布局 | 左右分栏，颜色区分 |
| 多阶段流程 | 手绘白板 + 拼接 | 每 2 阶段 1 张图 |
| 生活场景类比 | 手绘白板 | 快递、餐厅、钓鱼等也用手绘白板 |

---

## 注意事项

1. **智能跳过**：用户已提供表格时，直接跳过 Step 1，进入画图流程
2. **只用手绘白板**：所有内容一律使用手绘白板风格，禁止 kawaii/可爱风
3. **自动拆分**：多阶段流程（如锁升级）自动拆成多张图后拼接
4. **虚线框拼接**：多图使用 `--border-style dashed` 拼接成合集
5. **中文优先**：图内文字除专业术语外用中文
6. **批量处理**：多个问题时，每个问题单独生成 1 张图，不拼接
7. **布局限制**：拼接后最多 3 列（1×3、2×3、3×3）
8. **禁止风格**：小红书卡片、kawaii、粉嫩色系、大眼睛卡通、爱心星星装饰

---

## 完整示例

### 输入
```
图解：TCP 如何保证可靠传输？
```

### Step 1 输出（表格）

| 问题 | 技术回答 | 小白秒懂版 |
|------|----------|-----------|
| TCP 可靠传输 | 序列号确认、超时重传、滑动窗口、拥塞控制、校验和 | 发快递：包裹带单号→签收回执→没回就重发→看门口空间发多少→路堵就慢发→开箱验货 |

| 概念 | 口诀 |
|------|------|
| TCP 可靠传输 | 发货带单号，签收要回执，没回再重发 |

### Step 2 判断

- **风格**：手绘白板（唯一风格）
- **要点数量**：5 个 → **1 张图**（内容紧凑可合并）

### Step 3 生成图片

```bash
cd ~/.claude/skills/api-draw
python scripts/nanobanana_draw.py "Hand-drawn whiteboard sketch style diagram, 3:4 vertical ratio,
visual note-taking aesthetic, minimalist line art,
bold black marker strokes with blue highlight accents,
pure white background, clean and professional.

Title: 「TCP可靠传输：快递版」in bold hand-drawn style with blue underline.

Content with simple doodle icons:
1. 序列号+确认 - delivery person with numbered packages, receipt
2. 超时重传 - clock icon, retry arrow
3. 滑动窗口 - doorstep with space indicator
4. 拥塞控制 - truck in traffic, slow down sign
5. 校验和 - person checking box contents

Summary box: 口诀「发货带单号，签收要回执，没回再重发」
Excalidraw hand-drawn aesthetic, NOT cute/kawaii." \
  --style "手绘白板" \
  --subject "TCP可靠传输_快递版"
```

### Step 4 输出 MD

```markdown
# TCP 可靠传输图解

> 用发快递的思路理解 TCP 如何保证数据不丢失

## TCP 如何保证可靠传输？

**快递类比：**
1. **序列号+确认** = 包裹带单号，签收要回执
2. **超时重传** = 3天没签收？再发一个！
3. **滑动窗口** = 看门口空间发多少
4. **拥塞控制** = 双十一路堵，慢点发
5. **校验和** = 开箱验货

![TCP可靠传输](./assets/TCP可靠传输_快递版_0.png)

## 总结

| 概念 | 口诀 |
|------|------|
| TCP 可靠传输 | 发货带单号，签收要回执，没回再重发 |
```

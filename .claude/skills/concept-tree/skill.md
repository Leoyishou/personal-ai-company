---
name: concept-tree
description: "概念树生成器 - 用 Gemini 生成知识结构树，快速了解领域全貌。触发词：概念树、知识树、结构图"
---

# Concept Tree - 概念树生成器

<concept-tree>

## 触发条件

当用户想要了解某个概念、领域、产品的知识结构时使用。关键词：概念树、知识树、结构图、概念分解。

## 执行步骤

### 1. 获取用户输入的概念

从用户消息中提取要分析的概念/领域名称。如果不明确，询问用户。

### 2. 调用 Gemini 生成概念树

使用 OpenRouter API 调用 `google/gemini-2.5-pro-preview`：

```bash
source ~/.claude/secrets.env

cat > /tmp/concept_tree_prompt.json << 'JSONEOF'
{
  "model": "google/gemini-2.5-pro-preview",
  "messages": [
    {
      "role": "user",
      "content": "你是一个知识架构专家。请为「{用户输入的概念}」生成一个完整的概念树。\n\n要求：\n1. 使用树形结构（目录树格式），用 / 表示有子节点\n2. 每个概念后面用括号标注英文或解释，如：媒体库(MediaLibrary)\n3. 重要/核心概念用 ✅ 标记\n4. 用 * 标记可以有多个实例的节点\n5. 层级深度 3-5 层，涵盖该领域的核心概念\n6. 按逻辑关系组织，不是简单罗列\n\n完整参考示例（CapCut 剪映）：\n```\nCapCut_剪映/\n└── Project(工程)/\n    ├── Workspace(工作区)/\n    │   ├── MediaLibrary(媒体库/素材区)/\n    │   │   ├── Import(导入)/\n    │   │   │   ├── LocalFiles(本地文件)\n    │   │   │   ├── Album(相册)\n    │   │   │   └── Record(录制/录音)\n    │   │   ├── Assets(素材资产)/\n    │   │   │   ├── Video(视频)✅\n    │   │   │   ├── Audio(音频)✅\n    │   │   │   ├── Image(图片)✅\n    │   │   │   └── TextMaterials(字体/文本素材)✅\n    │   │   ├── Templates(模板/草稿同款)/\n    │   │   └── Favorites(收藏)\n    │   │\n    │   ├── Timeline(时间线)/\n    │   │   ├── Sequence(序列/主时间轴)/\n    │   │   │   ├── Track(轨道)* /\n    │   │   │   │   ├── VideoTrack(视频轨)✅\n    │   │   │   │   ├── AudioTrack(音频轨)✅\n    │   │   │   │   └── ...\n```\n\n请参考以上示例的深度、结构和标注风格，为用户输入的概念生成类似的概念树。直接输出概念树，不要有多余解释。"
    }
  ]
}
JSONEOF

curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d @/tmp/concept_tree_prompt.json | jq -r '.choices[0].message.content'
```

### 3. 生成交付物

将概念树保存为 Markdown 文件：

**文件路径**: `~/Desktop/{概念名}_concept_tree.md`

**文件格式**:

```markdown
# {概念名} 概念树

> 生成时间: {当前日期}
> 模型: Gemini 2.5 Pro

## 概念树

```
{生成的概念树内容}
```

## 图例

- `/` 表示该节点有子节点
- `✅` 表示核心/重要概念
- `*` 表示可以有多个实例

## 使用说明

这个概念树展示了 {概念名} 领域的知识结构，可用于：
- 快速了解领域全貌
- 学习路径规划
- 知识查漏补缺
```

### 4. 输出结果

1. 在终端展示概念树
2. 告知用户文件已保存到桌面

## 示例

用户：「给我 React 的概念树」

执行流程：
1. 调用 Gemini 生成 React 概念树
2. 保存到 `~/Desktop/React_concept_tree.md`
3. 展示概念树并告知文件位置

</concept-tree>

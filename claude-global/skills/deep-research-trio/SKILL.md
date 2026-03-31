# Deep Research Trio

并行触发 Gemini、ChatGPT、Claude 三家的 Deep Research 功能，并汇总结果。

## 触发方式

当用户需要深度调研某个话题，且希望获得多个 AI 的视角时使用此 skill。

触发词：
- "三家对比调研"
- "parallel deep research"
- "深度调研三巨头"
- "gemini chatgpt claude 一起调研"

## 前置条件

1. **Debug Chrome 运行中**：终端运行 `chrome-debug`
2. **已登录三个平台**：在 Debug Chrome 中登录 Gemini、ChatGPT、Claude
3. **订阅要求**：
   - ChatGPT Plus/Pro（Deep Research 需要）
   - Claude Max（Research 模式需要）
   - Gemini Advanced（可选，免费版也有 Deep Research）

## 使用方法

### 检查登录状态
```bash
cd ~/.claude/skills/deep-research-trio
node run.js status
```

### 运行深度调研
```bash
# 全部三个平台
node run.js research "AI Agent 技术趋势分析"

# 指定平台
node run.js research "React vs Vue 2025" -p gemini,chatgpt

# 单平台测试
node run.js research "测试问题" -p gemini
```

## 输出

- `reports/research-{timestamp}.json` - 原始结果
- `reports/research-{timestamp}.md` - Markdown 报告

### 报告结构

```markdown
# Deep Research Trio Report

## Summary
| Platform | Status | Duration |

## Detailed Results
### Gemini
- Summary
- Citations
- Full Response

### ChatGPT
...

### Claude
...
```

## 聚合分析

生成对比分析报告：
```bash
python scripts/aggregate_reports.py
```

输出 `reports/aggregate-{timestamp}.md`，包含：
- 共识点（2+ 平台提及）
- 各平台独特观点
- 引用来源对比

## 注意事项

1. Deep Research 耗时较长（5-60 分钟），请耐心等待
2. 使用 3 次稳定检测确保结果完整
3. 超时会返回部分结果，不会丢失已获取内容
4. 错误时自动截图保存到 `reports/` 目录

## 架构

```
deep-research-trio/
├── run.js                    # 主入口
├── lib/
│   ├── config.js            # 平台配置
│   ├── helpers.js           # 浏览器工具
│   ├── parallel-executor.js # 并行编排
│   └── stability-detector.js# 完成检测
├── platforms/
│   ├── base-platform.js     # 抽象基类
│   ├── gemini.js
│   ├── chatgpt.js
│   └── claude.js
└── scripts/
    └── aggregate_reports.py # 报告聚合
```

## 更新日志

### 2026-02-04
- **ChatGPT**: 更新 Deep Research 入口选择器
  - 点击 "+" 按钮打开附件菜单
  - 在下拉菜单中选择 "Deep research"
  - 添加 Deep Research 模式专用输入框选择器（placeholder: "Get a detailed report"）
- **Gemini**: 更新 Deep Research 完整流程
  - 点击 "Tools" 按钮打开工具菜单
  - 选择 "Deep Research"
  - **新增**：显示研究计划后，自动点击"开始研究"按钮
  - 调整流程顺序：先启用模式，再输入查询

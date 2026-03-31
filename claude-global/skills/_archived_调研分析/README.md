# Research Skill - 通用智能调研助手

## 简介

Research Skill 是一个强大的通用调研工具，支持多种调研模式，能够根据不同的调研需求自动选择合适的策略，并生成结构化的调研报告。

## 功能特点

- 🎯 **多模式支持**：技术、市场、竞品、人物、事件、行业、学术、投资等8种调研模式
- 🤖 **智能策略**：自动识别调研类型，选择最优调研路径
- 📊 **分析框架**：内置SWOT、Porter五力、PEST等专业分析框架
- 📝 **报告生成**：自动生成结构化的调研报告，包含执行摘要、详细分析和行动建议
- 💡 **洞见提取**：智能提取关键洞见和策略建议
- 🔄 **持续监测**：支持对特定主题的持续跟踪和监测

## 快速开始

### 基础用法

```bash
# 自动模式调研
skill research "OpenAI GPT-4"

# 指定技术调研
skill research --mode tech "React vs Vue"

# 市场调研
skill research --mode market "AI助手市场分析"

# 竞品分析
skill research --mode competitor "ChatGPT vs Claude"

# 人物调研
skill research --mode person "Sam Altman"
```

### 调研深度控制

```bash
# 快速调研（5分钟内）
skill research --quick "量子计算"

# 标准调研（15分钟）
skill research "区块链技术"

# 深度调研（30分钟）
skill research --depth deep "元宇宙生态"

# 全面调研（60分钟）
skill research --depth comprehensive "人工智能产业链"
```

### 使用分析框架

```bash
# 使用SWOT分析
skill research --framework swot "Tesla 电动汽车"

# 使用波特五力模型
skill research --framework porter "在线教育行业"

# 使用PEST分析
skill research --framework pest "新能源政策影响"
```

## 输出示例

调研完成后，会生成包含以下内容的报告：

1. **执行摘要**
   - 核心发现
   - 关键数据
   - 主要结论
   - 行动建议

2. **详细分析**
   - 现状评估
   - 深度分析
   - 对比研究
   - 趋势预测

3. **洞见与建议**
   - 关键洞见
   - 策略建议
   - 实施路径
   - 风险评估

4. **附录资料**
   - 数据来源
   - 参考文献
   - 术语解释

## 文件结构

```
~/.claude/skills/research/
├── skill.md           # Skill定义文件
├── research.py        # 核心调研逻辑
├── report_generator.py # 报告生成器
├── config.json        # 配置文件
└── README.md         # 使用说明
```

## 配置说明

可以通过编辑 `config.json` 文件来自定义调研行为：

```json
{
  "default_mode": "auto",        // 默认调研模式
  "default_depth": "standard",   // 默认调研深度
  "save_reports": true,          // 是否保存报告
  "report_path": "~/research_reports/",  // 报告保存路径
  "language": "zh-CN"           // 输出语言
}
```

## 高级功能

### 持续监测

```bash
# 每天监测一次
skill research --monitor "AI发展动态" --interval daily

# 每周监测
skill research --monitor "竞品更新" --interval weekly
```

### 对比研究

```bash
# 多主体对比
skill research --compare "React vs Vue vs Angular"

# 时间对比
skill research --history "比特币" --from 2020 --to 2024
```

### 趋势预测

```bash
# 5年预测
skill research --predict "自动驾驶" --horizon 5years

# 技术成熟度预测
skill research --predict "量子计算商用" --type maturity
```

## 输出格式

支持多种输出格式：

- **Markdown**（默认）：适合阅读和分享
- **JSON**：结构化数据，便于程序处理
- **HTML**：可直接在浏览器中查看
- **PDF**：专业报告格式（需要额外依赖）

## 最佳实践

1. **明确目标**：调研前明确你想要了解什么
2. **选择模式**：根据需求选择合适的调研模式
3. **控制深度**：平衡调研深度和时间成本
4. **验证信息**：重要决策前进行多源验证
5. **持续更新**：定期更新调研结果

## 注意事项

- 调研结果基于公开可获取的信息
- 需要网络连接以获取最新数据
- 部分功能可能需要配置API密钥
- 遵守相关法律法规和道德规范

## 问题反馈

如遇到问题或有改进建议，请：

1. 检查配置文件是否正确
2. 查看错误日志
3. 参考使用示例
4. 提交问题描述

## 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 支持8种调研模式
- 内置专业分析框架
- 自动报告生成功能

## 许可证

本工具仅供学习和研究使用。
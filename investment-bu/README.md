# 投资事业部 - 资本杠杆

> 管理投资，事件驱动，放大资金

## 一、核心信息

| 字段 | 值 |
|------|-----|
| Linear Team | I (投资事业部) |
| Initiative | 资本杠杆 |
| 启动命令 | `cd ~/usr/pac/investment-bu && claude --dangerously-skip-permissions` |

## 二、投资类型（Linear Project）

| 项目 | 说明 |
|------|------|
| 美股 | 美股交易与调研 |
| 港股 | 港股交易与调研 |
| 加密货币 | 数字资产 |
| 其他资产 | 债券、期权等 |

## 三、标签

### 活动类型

| 标签 | 说明 |
|------|------|
| 交易 | 实际买入/卖出 |
| 调研 | 深度研究分析 |
| 复盘 | 交易复盘、策略检验 |
| 观察 | 加入观察列表 |

### 决策依据

基本面 / 技术面 / 情绪面 / 事件驱动

## 四、目录结构

```
investment-bu/
├── hooks/                 # 交易检测 hooks
└── inbox/                 # 临时项目
```

## 五、自动化

### 5.1 交易检测

`futu-trades` skill 输出含"买入/卖出/成交" --> 创建交易 Issue

### 5.2 调研关联交易

同一 Session 先调研后交易 --> 自动关联两个 Issue

### 5.3 复盘提醒

交易后 7 天自动创建复盘提醒

## 六、常用 Skills

| Skill | 用途 |
|-------|------|
| `futu-trades` | 查询富途证券交易/持仓 |
| `research` | 深度调研 |
| `lakehouse` | DuckDB 数据分析 |
| `KOL-info-collect` | Telegram 投资群信息 |

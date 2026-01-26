---
name: futu-trades
description: "查询富途证券最近的交易记录、持仓和账户信息。需要本地运行 FutuOpenD 服务。"
---

# 富途交易查询 Skill

通过调用富途 OpenD API 获取交易数据。

## 使用场景

当用户想要查看交易记录时使用：

- "查看最近的交易记录"
- "我最近买卖了什么股票"
- "查看持仓"
- "账户情况怎么样"

## 前置条件

1. 本地需要运行 FutuOpenD 服务（默认端口 11111）
2. 已安装 `futu-api` Python 包

## 命令结构

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py [OPTIONS]
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--days N` | 获取最近 N 天的交易记录 | 7 |
| `--positions` | 获取当前持仓 | - |
| `--account` | 获取账户信息 | - |
| `--market` | 交易市场：US/HK/CN | US |
| `--test` | 测试连接 | - |

## 使用示例

1. **查看最近 7 天交易记录**（默认）

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py
```

2. **查看最近 30 天交易记录**

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py --days 30
```

3. **查看当前持仓**

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py --positions
```

4. **查看账户信息**

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py --account
```

5. **查看港股交易记录**

```bash
python3 /Users/liuyishou/.claude/skills/futu-trades/scripts/futu_trades.py --market HK
```

## 输出格式

脚本输出 JSON 格式数据，方便解析和展示。

### 交易记录示例

```json
{
  "trades": [
    {
      "order_id": "123456",
      "stock_code": "US.AAPL",
      "stock_name": "苹果",
      "trade_time": "2025-01-20 10:30:00",
      "trade_type": "BUY",
      "price": 150.5,
      "quantity": 100,
      "amount": 15050.0
    }
  ],
  "summary": {
    "total_trades": 10,
    "buy_count": 5,
    "sell_count": 5
  }
}
```

## 注意事项

- 需要确保 FutuOpenD 已启动并登录
- 默认连接 127.0.0.1:11111
- 默认查询实盘环境，如需模拟盘请修改脚本配置

#!/usr/bin/env python3
"""
富途交易查询脚本 - 用于 Claude Code Skill
查询交易记录、持仓和账户信息
"""

from futu import *
import json
import argparse
import sys
from datetime import datetime, timedelta
import pytz

# 配置
FUTU_HOST = "127.0.0.1"
FUTU_PORT = 11111
TRD_ENV = TrdEnv.REAL  # 实盘

MARKET_MAP = {
    "US": TrdMarket.US,
    "HK": TrdMarket.HK,
    "CN": TrdMarket.CN,
}


class FutuQuery:
    def __init__(self, market="US"):
        self.trd_market = MARKET_MAP.get(market.upper(), TrdMarket.US)
        self.trade_ctx = None

    def connect(self):
        try:
            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=self.trd_market,
                host=FUTU_HOST,
                port=FUTU_PORT
            )
            return True
        except Exception as e:
            return False

    def _safe_float(self, value, default=0.0):
        try:
            if value is None or value == "N/A" or value == "":
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0):
        try:
            if value is None or value == "N/A" or value == "":
                return default
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_trades(self, days=7):
        """获取交易记录"""
        if not self.trade_ctx:
            return {"error": "未连接"}

        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=days)
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

            ret, data = self.trade_ctx.history_deal_list_query(
                start=start_str, end=end_str, trd_env=TRD_ENV
            )

            if ret == RET_OK:
                if hasattr(data, 'empty') and data.empty:
                    return {"trades": [], "summary": {"total_trades": 0, "buy_count": 0, "sell_count": 0}}

                trades = []
                buy_count = 0
                sell_count = 0

                for _, row in data.iterrows():
                    trade_type = "BUY" if row.get("trd_side", "") == "BUY" else "SELL"
                    if trade_type == "BUY":
                        buy_count += 1
                    else:
                        sell_count += 1

                    trade = {
                        "order_id": str(row.get("deal_id", "")),
                        "stock_code": row.get("code", ""),
                        "stock_name": row.get("name", ""),
                        "trade_time": row.get("create_time", ""),
                        "trade_type": trade_type,
                        "price": self._safe_float(row.get("price", 0)),
                        "quantity": self._safe_int(row.get("qty", 0)),
                        "amount": self._safe_float(row.get("price", 0)) * self._safe_int(row.get("qty", 0)),
                    }
                    trades.append(trade)

                return {
                    "trades": trades,
                    "summary": {
                        "total_trades": len(trades),
                        "buy_count": buy_count,
                        "sell_count": sell_count
                    }
                }
            else:
                return {"error": f"查询失败: {data}"}

        except Exception as e:
            return {"error": str(e)}

    def get_positions(self):
        """获取持仓"""
        if not self.trade_ctx:
            return {"error": "未连接"}

        try:
            ret, data = self.trade_ctx.position_list_query(trd_env=TRD_ENV)

            if ret == RET_OK:
                if hasattr(data, 'empty') and data.empty:
                    return {"positions": [], "summary": {"total_count": 0, "total_value": 0, "total_profit": 0}}

                positions = []
                total_value = 0
                total_profit = 0

                for _, row in data.iterrows():
                    market_val = self._safe_float(row.get("market_val", 0))
                    profit = self._safe_float(row.get("pl_val", 0))
                    total_value += market_val
                    total_profit += profit

                    position = {
                        "stock_code": row.get("code", ""),
                        "stock_name": row.get("stock_name", ""),
                        "quantity": self._safe_int(row.get("qty", 0)),
                        "avg_cost": self._safe_float(row.get("cost_price", 0)),
                        "current_price": self._safe_float(row.get("last_price", 0)),
                        "market_value": market_val,
                        "profit": profit,
                        "profit_rate": self._safe_float(row.get("pl_ratio", 0)) * 100,  # 转为百分比
                    }
                    positions.append(position)

                return {
                    "positions": positions,
                    "summary": {
                        "total_count": len(positions),
                        "total_value": round(total_value, 2),
                        "total_profit": round(total_profit, 2)
                    }
                }
            else:
                return {"error": f"查询失败: {data}"}

        except Exception as e:
            return {"error": str(e)}

    def get_account(self):
        """获取账户信息"""
        if not self.trade_ctx:
            return {"error": "未连接"}

        try:
            ret, data = self.trade_ctx.accinfo_query(trd_env=TRD_ENV)

            if ret == RET_OK:
                if hasattr(data, 'empty') and not data.empty:
                    acc = data.iloc[0]
                    return {
                        "total_assets": self._safe_float(acc.get("total_assets", 0)),
                        "available_cash": self._safe_float(acc.get("cash", 0)),
                        "position_value": self._safe_float(acc.get("market_val", 0)),
                        "unrealized_pl": self._safe_float(acc.get("unrealized_pl", 0)),
                        "realized_pl": self._safe_float(acc.get("realized_pl", 0)),
                    }
                else:
                    return {"error": "无账户数据"}
            else:
                return {"error": f"查询失败: {data}"}

        except Exception as e:
            return {"error": str(e)}

    def close(self):
        if self.trade_ctx:
            self.trade_ctx.close()


def main():
    parser = argparse.ArgumentParser(description='富途交易查询')
    parser.add_argument('--days', type=int, default=7, help='获取最近N天的交易记录')
    parser.add_argument('--positions', action='store_true', help='获取持仓')
    parser.add_argument('--account', action='store_true', help='获取账户信息')
    parser.add_argument('--market', type=str, default='US', help='市场：US/HK/CN')
    parser.add_argument('--test', action='store_true', help='测试连接')

    args = parser.parse_args()

    query = FutuQuery(market=args.market)

    if not query.connect():
        print(json.dumps({"error": "连接 FutuOpenD 失败，请确保服务已启动"}, ensure_ascii=False))
        sys.exit(1)

    try:
        if args.test:
            print(json.dumps({"success": True, "message": "连接成功"}, ensure_ascii=False))
        elif args.positions:
            result = query.get_positions()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.account:
            result = query.get_account()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            result = query.get_trades(days=args.days)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        query.close()


if __name__ == "__main__":
    main()

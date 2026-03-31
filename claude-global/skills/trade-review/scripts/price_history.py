#!/usr/bin/env python3
"""
价格历史查询 - 用于 trade-review skill
查询标的在指定时间段的收盘价序列，辅助判断支点是否兑现
"""

import argparse
import json
import sys

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance 未安装，运行: pip install yfinance"}))
    sys.exit(1)


def get_price_history(ticker: str, start: str, end: str):
    """获取标的历史价格"""
    t = yf.Ticker(ticker)
    hist = t.history(start=start, end=end)

    if hist.empty:
        return {"error": f"无数据：{ticker}，检查代码格式（港股用 9927.HK）"}

    prices = []
    for date, row in hist.iterrows():
        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "close": round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
            "change_pct": None,  # 填充在下方
        })

    # 计算日涨跌幅
    for i in range(1, len(prices)):
        prev = prices[i - 1]["close"]
        curr = prices[i]["close"]
        prices[i]["change_pct"] = round((curr - prev) / prev * 100, 2)

    # 统计
    first_close = prices[0]["close"]
    last_close = prices[-1]["close"]
    total_return = round((last_close - first_close) / first_close * 100, 2)
    max_close = max(p["close"] for p in prices)
    min_close = min(p["close"] for p in prices)

    return {
        "ticker": ticker,
        "start": prices[0]["date"],
        "end": prices[-1]["date"],
        "first_close": first_close,
        "last_close": last_close,
        "total_return_pct": total_return,
        "max_close": max_close,
        "min_close": min_close,
        "trading_days": len(prices),
        "prices": prices,
    }


def main():
    parser = argparse.ArgumentParser(description="历史价格查询")
    parser.add_argument("--ticker", required=True, help="股票代码，港股加.HK后缀（如9927.HK）")
    parser.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--summary-only", action="store_true", help="只输出摘要，不输出逐日数据")

    args = parser.parse_args()

    result = get_price_history(args.ticker, args.start, args.end)

    if args.summary_only and "prices" in result:
        del result["prices"]

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

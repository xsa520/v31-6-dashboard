import json
import pandas as pd
from collections import defaultdict

# 讀取交易紀錄
with open("data/trade_records.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

# 勝率計算（總勝率與各標的勝率）
pair_trades = defaultdict(list)
for t in trades:
    pair_trades[t["ticker"]].append(t)

total_win, total_count = 0, 0
symbol_stats = {}
for ticker, records in pair_trades.items():
    win, count = 0, 0
    buy_price = None
    for r in records:
        if r["action"] == "BUY":
            buy_price = r["price"]
        elif r["action"].startswith("SELL") and buy_price is not None:
            count += 1
            if r["price"] > buy_price:
                win += 1
            buy_price = None
    symbol_stats[ticker] = {"win": win, "count": count, "accuracy": win / count if count > 0 else 0}
    total_win += win
    total_count += count

total_accuracy = total_win / total_count if total_count > 0 else 0
print(f"總勝率: {total_accuracy:.2%} ({total_win}/{total_count})")
print("各標的勝率：")
for ticker, stat in symbol_stats.items():
    print(f"  {ticker}: {stat['accuracy']:.2%} ({stat['win']}/{stat['count']})")

# 讀取資本曲線
with open("data/capital_trend.json", "r", encoding="utf-8") as f:
    capital_trend = json.load(f)

df = pd.DataFrame(capital_trend)
df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date")

# 年化報酬率計算
start = df.iloc[0]["capital"]
end = df.iloc[-1]["capital"]
years = (df.index[-1] - df.index[0]).days / 365
annual_return = (end / start) ** (1 / years) - 1
print(f"年化報酬率: {annual_return:.2%}")

# 最大回撤計算
peak = df["capital"].iloc[0]
max_drawdown = 0
for c in df["capital"]:
    if c > peak:
        peak = c
    drawdown = (peak - c) / peak
    if drawdown > max_drawdown:
        max_drawdown = drawdown
print(f"最大回撤: {max_drawdown:.2%}")

# 每月最後一天的資本
monthly = df.resample("ME").last()
print("\n每月資本金額：")
print(monthly)
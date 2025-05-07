import json
import os
from datetime import datetime

# 假設真實交易記錄在此檔案
TRADE_LOG_FILE = "data/trade_log.json"
CAPITAL_TREND_FILE = "data/capital_trend.json"

def load_trade_log():
    if not os.path.exists(TRADE_LOG_FILE):
        return []
    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_by_day(trades):
    capital_summary = {}
    for trade in trades:
        date = trade["date"]
        capital = float(trade["portfolio_value"])  # 假設每筆記錄有當日資產總值
        capital_summary[date] = capital
    return [{"date": k, "capital": v} for k, v in sorted(capital_summary.items())]

def save_to_json(data):
    with open(CAPITAL_TREND_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    trades = load_trade_log()
    trend = summarize_by_day(trades)
    save_to_json(trend)
    print("✅ 已更新 capital_trend.json")

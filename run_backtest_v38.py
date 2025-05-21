import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime
from tqdm import tqdm
# === 新增：import 優化後的策略核心 ===
from strategy_core import (
    is_bull_market, is_bear_market,
    evaluate_buy, evaluate_sell,
    evaluate_short_sell, evaluate_short_cover
)

# === 策略參數設定 ===
START_DATE = "2000-01-01"
END_DATE = "2025-05-10"
INITIAL_CAPITAL = 10000
DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)

tickers = {
    "NVDA": 0.40,
    "TSLA": 0.15,
    "PLTR": 0.20,
    "CELH": 0.10,
    "AAPL": 0.15
}

# === 技術指標條件 ===
def fetch_data(symbol):
    print(f"下載 {symbol} 資料中...")
    df = yf.download(symbol, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)
    print(f"{symbol} 資料下載完成")
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA150"] = df["Close"].rolling(window=150).mean()
    df["Volume_MA"] = df["Volume"].rolling(window=20).mean()
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]
    # 新增RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df.dropna()

# === 主回測程式 ===
def run_backtest():
    print("run_backtest() 開始執行")
    capital = INITIAL_CAPITAL
    capital_trend = []
    trades = []

    for symbol in tqdm(tickers, desc="回測進度"):
        print(f"開始回測 {symbol}")
        df = fetch_data(symbol)
        print(f"{symbol} 資料下載完成，資料筆數：{len(df)}")
        if df.empty:
            print(f"{symbol} 無資料，跳過")
            continue
        position = None
        # 每一檔都分配固定資金池（分倉）
        available_cash = capital * 0.2
        for i in range(151, len(df)):
            if i % 10 == 0:
                print(f"{symbol} 處理到 {df.index[i].strftime('%Y-%m-%d')} (第 {i} 筆)")
            row = df.iloc[i]
            date_str = row.name.strftime("%Y-%m-%d")
            # 修正float用法
            ma50 = float(row["MA50"].item())
            ma150 = float(row["MA150"].item())
            macd = float(row["MACD"].item())
            macd_hist = float(row["MACD_Hist"].item())
            volume = float(row["Volume"].item())
            avg_volume = float(row["Volume_MA"].item())
            price = float(row["Close"].item())
            rsi = float(row["RSI"].item())
            prev_high = float(df["High"].iloc[i-20:i].max().item())
            prev_low = float(df["Low"].iloc[i-20:i].min().item())
            support = float(df["Low"].iloc[i-10:i].min().item())
            resistance = float(df["High"].iloc[i-10:i].max().item())

            # === 牛熊市判斷（傳兩個參數） ===
            is_bull = is_bull_market(df["MA150"].iloc[:i+1], df["MA50"].iloc[:i+1])
            is_bear = is_bear_market(df["MA150"].iloc[:i+1], df["MA50"].iloc[:i+1])

            if position:
                if position["type"] == "long":
                    profit = (price - position["entry_price"]) / position["entry_price"]
                    position["max_profit"] = max(position["max_profit"], profit)
                    sell_signal = evaluate_sell(
                        position["entry_price"], price, position["max_profit"], macd_hist, volume, avg_volume, position["support"]
                    )
                    if sell_signal.startswith("SELL"):
                        available_cash = max(0, available_cash + price * position["shares"])
                        trades.append({
                            "date": date_str, "ticker": symbol, "action": sell_signal,
                            "price": round(price, 2), "shares": position["shares"], "position_type": "long"
                        })
                        print(f"{symbol} 多單平倉於 {date_str}，價格：{price}")
                        position = None
                elif position["type"] == "short":
                    profit = (position["entry_price"] - price) / position["entry_price"]
                    position["max_profit"] = max(position["max_profit"], profit)
                    cover_signal = evaluate_short_cover(
                        position["entry_price"], price, position["max_profit"], macd_hist, volume, avg_volume, position["resistance"]
                    )
                    if cover_signal.startswith("COVER"):
                        available_cash = max(0, available_cash - price * position["shares"])
                        trades.append({
                            "date": date_str, "ticker": symbol, "action": cover_signal,
                            "price": round(price, 2), "shares": position["shares"], "position_type": "short"
                        })
                        print(f"{symbol} 空單平倉於 {date_str}，價格：{price}")
                        position = None
            if not position:
                if is_bull and evaluate_buy(price, ma50, ma150, macd, volume, avg_volume, prev_high, rsi):
                    max_risk_cap = available_cash
                    shares = int(max_risk_cap // price)
                    if shares > 0:
                        available_cash = max(0, available_cash - price * shares)
                        position = {
                            "type": "long",
                            "entry_price": price,
                            "shares": shares,
                            "max_profit": 0,
                            "support": prev_high
                        }
                        trades.append({
                            "date": date_str, "ticker": symbol, "action": "BUY",
                            "price": round(price, 2), "shares": shares, "position_type": "long"
                        })
                        print(f"{symbol} 多單進場於 {date_str}，價格：{price}")
                elif is_bear and evaluate_short_sell(price, ma50, ma150, macd, volume, avg_volume, prev_low, rsi):
                    max_risk_cap = available_cash
                    shares = int(max_risk_cap // price)
                    if shares > 0:
                        available_cash = max(0, available_cash + price * shares)
                        position = {
                            "type": "short",
                            "entry_price": price,
                            "shares": shares,
                            "max_profit": 0,
                            "resistance": prev_low
                        }
                        trades.append({
                            "date": date_str, "ticker": symbol, "action": "SHORT_SELL",
                            "price": round(price, 2), "shares": shares, "position_type": "short"
                        })
                        print(f"{symbol} 空單進場於 {date_str}，價格：{price}")
            # 記錄每日資本（現金+持倉市值）
            total_cap = available_cash
            if position:
                if position["type"] == "long":
                    total_cap += price * position["shares"]
                elif position["type"] == "short":
                    total_cap += max(0, position["entry_price"] - price) * position["shares"]
            capital_trend.append({"date": date_str, "capital": round(total_cap, 2)})
    with open(os.path.join(DATA_PATH, "capital_trend.json"), "w") as f:
        json.dump(capital_trend, f, indent=2)
    with open(os.path.join(DATA_PATH, "trade_records.json"), "w") as f:
        json.dump(trades, f, indent=2)
    print("回測完成，結果已儲存。")

# === 績效計算 ===
def calc_performance(capital_data):
    if not capital_data:
        print("無資本資料")
        return
    start = capital_data[0]
    end = capital_data[-1]
    start_date = datetime.strptime(start["date"], "%Y-%m-%d")
    end_date = datetime.strptime(end["date"], "%Y-%m-%d")
    years = (end_date - start_date).days / 365
    print("start capital:", start["capital"])
    print("end capital:", end["capital"])
    print("years:", years)
    if start["capital"] <= 0 or end["capital"] <= 0 or years <= 0:
        print("資本或年數異常，無法計算年化報酬率")
        return
    ratio = end["capital"] / start["capital"]
    if ratio <= 0:
        print("資本比值異常，無法計算年化報酬率")
        return
    annual_return = ratio ** (1 / years) - 1
    annual_return = annual_return.real  # 強制取實數部分
    peak = start["capital"]
    max_drawdown = 0
    for c in capital_data:
        if c["capital"] > peak:
            peak = c["capital"]
        drawdown = (peak - c["capital"]) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    print(f"年化報酬率: {annual_return:.2%}")
    print(f"最大回撤: {max_drawdown:.2%}")

if __name__ == "__main__":
    run_backtest()
    with open(os.path.join(DATA_PATH, "capital_trend.json"), "r") as f:
        capital_trend = json.load(f)
    calc_performance(capital_trend)
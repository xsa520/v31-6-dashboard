import yfinance as yf
import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime
from telegram_utils import send_trade_notify, send_guardian_notify
from strategy_core import (
    dynamic_stock_selection, get_selected_pool,
    evaluate_buy, evaluate_sell, evaluate_short_sell, evaluate_short_cover,
    is_bull_market, is_bear_market
)
import traceback  # <--- 新增

CHECK_INTERVAL = 60  # 每1分鐘檢查一次
INITIAL_CAPITAL = 100000
TOP_N = 5
DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)

def to_float(x):
    if isinstance(x, pd.Series) or isinstance(x, np.ndarray):
        if hasattr(x, 'iloc') and x.size == 1:
            return float(x.iloc[0])
        return float(np.ravel(x)[-1])
    return float(x)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)
def fetch_realtime_data(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1m", progress=False, auto_adjust=True)
        if df.empty:
            return None
        df["MA50"] = df["Close"].rolling(window=50).mean()
        df["MA150"] = df["Close"].rolling(window=150).mean()
        df["Volume_MA"] = df["Volume"].rolling(window=20).mean()
        df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
        df["Signal"] = df["MACD"].ewm(span=9).mean()
        df["MACD_Hist"] = df["MACD"] - df["Signal"]
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        return df.dropna()
    except Exception as e:
        print(f"下載 {symbol} 即時資料失敗：{e}")
        return None

def get_topN_stocks():
    dynamic_tickers = dynamic_stock_selection()
    selected_pool = get_selected_pool()
    tickers_to_pick = list(set(dynamic_tickers) & set(selected_pool))
    stock_scores = []
    for symbol in tickers_to_pick:
        try:
            df = yf.download(symbol, period="2y", interval="1d", progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            cagr = (df['Close'].iloc[-1] / df['Close'].iloc[0]) ** (252/len(df)) - 1
            score = float(cagr)  # <--- 強制轉 float，避免 Series 比較錯誤
            stock_scores.append((symbol, score))
        except Exception as e:
            print(f"過濾/回測異常：{symbol}，錯誤：{e}")
            continue
    stock_scores.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in stock_scores[:TOP_N]]

def update_portfolio(portfolio, topN, prices, capital):
    new_portfolio = {}
    per_stock_cap = capital / TOP_N
    actions = []
    # 平倉不在 topN 的股票
    for symbol in list(portfolio.keys()):
        if symbol not in topN:
            close_price = prices.get(symbol, None)
            if close_price:
                actions.append(f"賣出 {symbol}，價格：{close_price}")
                send_trade_notify(f"賣出 {symbol}，價格：{close_price}")
            capital += portfolio[symbol]['shares'] * close_price
            del portfolio[symbol]
    # 建倉/加碼 topN 股票
    for symbol in topN:
        price = prices.get(symbol, None)
        if not price:
            continue
        shares = int(per_stock_cap // price)
        if shares > 0:
            new_portfolio[symbol] = {'shares': shares, 'entry_price': price}
            if symbol not in portfolio:
                actions.append(f"買入 {symbol}，價格：{price}，股數：{shares}")
                send_trade_notify(f"買入 {symbol}，價格：{price}，股數：{shares}")
    return new_portfolio, capital, actions
if __name__ == "__main__":
    print("=== 這是 2024/06/09 追蹤traceback強化+Series比較修正版 ===")
    print("即時虛擬交易啟動，每1分鐘檢查一次...")

    # 初始化資本、持倉、紀錄
    capital = INITIAL_CAPITAL
    portfolio = load_json(os.path.join(DATA_PATH, "virtual_portfolio.json"), {})
    capital_trend = load_json(os.path.join(DATA_PATH, "virtual_capital_trend.json"), [])
    trade_records = load_json(os.path.join(DATA_PATH, "virtual_trade_records.json"), [])

    while True:
        try:
            # 1. 選股
            topN = get_topN_stocks()
            print(f"{datetime.now()} 本次選股：{topN}")

            # 2. 取得最新價格
            prices = {}
            for symbol in topN + list(portfolio.keys()):
                df = fetch_realtime_data(symbol)
                if df is not None and not df.empty:
                    row = df.iloc[-1]
                    # 這裡直接用 to_float 處理所有欄位
                    ma50 = to_float(row["MA50"])
                    ma150 = to_float(row["MA150"])
                    is_bull = is_bull_market(to_float(ma150), to_float(ma50))
                    is_bear = is_bear_market(to_float(ma150), to_float(ma50))
                    prices[symbol] = float(row['Close'])
                    # 你可以根據 is_bull/is_bear 做進階判斷
                else:
                    print(f"無法取得 {symbol} 最新價，跳過")
            
            # 3. 持倉管理與再平衡
            new_portfolio, capital, actions = update_portfolio(portfolio, topN, prices, capital)
            portfolio = new_portfolio

            # 4. 記錄資本走勢
            total_value = capital
            for symbol, pos in portfolio.items():
                price = prices.get(symbol, pos['entry_price'])
                total_value += pos['shares'] * price
            capital_trend.append({
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "capital": round(total_value, 2)
            })

            # 5. 記錄交易
            for act in actions:
                trade_records.append({
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": act
                })

            # 6. 儲存紀錄
            save_json(os.path.join(DATA_PATH, "virtual_portfolio.json"), portfolio)
            save_json(os.path.join(DATA_PATH, "virtual_capital_trend.json"), capital_trend)
            save_json(os.path.join(DATA_PATH, "virtual_trade_records.json"), trade_records)

            # 7. 每日推播總結（可依需求調整頻率）
            if datetime.now().hour == 6 and datetime.now().minute < 2:
                msg = f"【每日總結】\n資本：{round(total_value,2)}\n持倉：{list(portfolio.keys())}\n今日交易：{actions if actions else '無'}"
                send_guardian_notify(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("=== 這是完整錯誤追蹤 ===")
            print(traceback.format_exc())
            send_guardian_notify(f"主迴圈異常：{e}\n{traceback.format_exc()}")
            time.sleep(CHECK_INTERVAL)

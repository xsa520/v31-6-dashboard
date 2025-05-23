import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime
from tqdm import tqdm
from telegram_utils import send_trade_notify, send_guardian_notify
from strategy_core import (
    is_bull_market, is_bear_market,
    evaluate_buy, evaluate_sell,
    evaluate_short_sell, evaluate_short_cover,
    dynamic_stock_selection, get_selected_pool
)
from apscheduler.schedulers.blocking import BlockingScheduler
import time

def to_float(x):
    import numpy as np
    import pandas as pd
    if isinstance(x, pd.Series) or isinstance(x, np.ndarray):
        if hasattr(x, 'iloc') and x.size == 1:
            return float(x.iloc[0])
        return float(np.ravel(x)[-1])
    return float(x)

START_DATE = "2000-01-01"
END_DATE = "2025-05-10"
INITIAL_CAPITAL = 10000
DATA_PATH = "data"
AI_LEARN_LOG = os.path.join(DATA_PATH, "ai_learn_log.json")
os.makedirs(DATA_PATH, exist_ok=True)

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
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df.dropna()

def log_ai_learning(event, detail):
    log = []
    if os.path.exists(AI_LEARN_LOG):
        with open(AI_LEARN_LOG, "r") as f:
            log = json.load(f)
    log.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "detail": detail
    })
    with open(AI_LEARN_LOG, "w") as f:
        json.dump(log, f, indent=2)

def push_ai_learning_summary():
    """定期推播AI學習摘要"""
    if not os.path.exists(AI_LEARN_LOG):
        return
    with open(AI_LEARN_LOG, "r") as f:
        log = json.load(f)
    if not log:
        return
    summary = "V38 AI學習紀錄摘要：\n"
    for item in log[-10:]:  # 只推播最近10筆
        summary += f"{item['time']} | {item['event']} | {item['detail']}\n"
    print(f"[推播] send_guardian_notify: {summary}")
    send_guardian_notify(summary)
def run_backtest():
    print("run_backtest() 開始執行")
    capital = INITIAL_CAPITAL
    capital_trend = []
    trades = []

    # === 雙核心混合模式：動態選股 + 精選池交集 ===
    dynamic_tickers = dynamic_stock_selection()
    selected_pool = get_selected_pool()
    tickers_to_trade = list(set(dynamic_tickers) & set(selected_pool))
    print("本次交集選股：", tickers_to_trade)
    for symbol in tqdm(tickers_to_trade, desc="回測進度"):
        try:
            print(f"開始回測 {symbol}")
            df = fetch_data(symbol)
            print(f"{symbol} 資料下載完成，資料筆數：{len(df)}")
            if df.empty:
                print(f"{symbol} 無資料，跳過")
                continue
            position = None
            available_cash = capital * 0.2
            for i in range(151, len(df)):
                row = df.iloc[i]
                date_str = row.name.strftime("%Y-%m-%d")
                print(f"檢查 {symbol} {date_str}，現價：{row['Close']}")
                ma50 = to_float(row["MA50"])
                ma150 = to_float(row["MA150"])
                macd = to_float(row["MACD"])
                macd_hist = to_float(row["MACD_Hist"])
                volume = to_float(row["Volume"])
                avg_volume = to_float(row["Volume_MA"])
                price = to_float(row["Close"])
                rsi = to_float(row["RSI"])
                prev_high = to_float(df["High"].iloc[i-20:i].max())
                prev_low = to_float(df["Low"].iloc[i-20:i].min())
                support = to_float(df["Low"].iloc[i-10:i].min())
                resistance = to_float(df["High"].iloc[i-10:i].max())
                is_bull = is_bull_market(df["MA150"].iloc[i], df["MA50"].iloc[i])
                is_bear = is_bear_market(df["MA150"].iloc[i], df["MA50"].iloc[i])

                if i > 1 and (df['Close'].iloc[i] - df['Close'].iloc[i-1]) / df['Close'].iloc[i-1] < -0.08:
                    print(f"[推播] send_trade_notify: ⚠️ 黑天鵝警示：{symbol} {date_str} 單日跌幅超過8%")
                    send_trade_notify(f"⚠️ 黑天鵝警示：{symbol} {date_str} 單日跌幅超過8%")
                    log_ai_learning("黑天鵝警示", f"{symbol} {date_str} 單日跌幅超過8%")
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
                            print(f"[推播] send_trade_notify: 賣出訊號：{symbol}，價格：{price}，日期：{date_str}")
                            send_trade_notify(f"賣出訊號：{symbol}，價格：{price}，日期：{date_str}")
                            if sell_signal == "SELL_STOP_LOSS":
                                print(f"[推播] send_guardian_notify: ⚠️ {symbol} 多單觸發止損，日期：{date_str}，價格：{price}")
                                send_guardian_notify(f"⚠️ {symbol} 多單觸發止損，日期：{date_str}，價格：{price}")
                                log_ai_learning("多單止損", f"{symbol} {date_str} {price}")
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
                            print(f"[推播] send_trade_notify: 回補訊號：{symbol}，價格：{price}，日期：{date_str}")
                            send_trade_notify(f"回補訊號：{symbol}，價格：{price}，日期：{date_str}")
                            if cover_signal == "COVER_STOP_LOSS":
                                print(f"[推播] send_guardian_notify: ⚠️ {symbol} 空單觸發止損，日期：{date_str}，價格：{price}")
                                send_guardian_notify(f"⚠️ {symbol} 空單觸發止損，日期：{date_str}，價格：{price}")
                                log_ai_learning("空單止損", f"{symbol} {date_str} {price}")
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
                            print(f"[推播] send_trade_notify: 買入訊號：{symbol}，價格：{price}，日期：{date_str}")
                            send_trade_notify(f"買入訊號：{symbol}，價格：{price}，日期：{date_str}")
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
                            print(f"[推播] send_trade_notify: 放空訊號：{symbol}，價格：{price}，日期：{date_str}")
                            send_trade_notify(f"放空訊號：{symbol}，價格：{price}，日期：{date_str}")
                total_cap = available_cash
                if position:
                    if position["type"] == "long":
                        total_cap += price * position["shares"]
                    elif position["type"] == "short":
                        total_cap += max(0, position["entry_price"] - price) * position["shares"]
                capital_trend.append({"date": date_str, "capital": round(total_cap, 2)})
        except Exception as e:
            print(f"[推播] send_guardian_notify: ❌ 策略異常：{symbol}，錯誤：{e}")
            send_guardian_notify(f"❌ 策略異常：{symbol}，錯誤：{e}")
            log_ai_learning("策略異常", f"{symbol} {e}")
    with open(os.path.join(DATA_PATH, "capital_trend.json"), "w") as f:
        json.dump(capital_trend, f, indent=2)
    with open(os.path.join(DATA_PATH, "trade_records.json"), "w") as f:
        json.dump(trades, f, indent=2)
    print("回測完成，結果已儲存。")

    # 新增推播：無論有無交易都推播
    print("[推播] send_guardian_notify: ✅ V38 策略主流程已執行完畢（不論有無交易）")
    send_guardian_notify("✅ V38 策略主流程已執行完畢（不論有無交易）")

    pd.DataFrame(capital_trend).to_csv(os.path.join(DATA_PATH, "account_history.csv"), index=False, encoding="utf-8")
    pd.DataFrame(trades).to_csv(os.path.join(DATA_PATH, "trade_records.csv"), index=False, encoding="utf-8")
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
    annual_return = annual_return.real
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

def job_backtest():
    # 清除舊的交易紀錄
    if os.path.exists(os.path.join(DATA_PATH, "capital_trend.json")):
        os.remove(os.path.join(DATA_PATH, "capital_trend.json"))
    if os.path.exists(os.path.join(DATA_PATH, "trade_records.json")):
        os.remove(os.path.join(DATA_PATH, "trade_records.json"))
    if os.path.exists(AI_LEARN_LOG):
        os.remove(AI_LEARN_LOG)

    print("[推播] send_trade_notify: V38 策略已於美股開市前20分鐘自動啟動！")
    send_trade_notify("V38 策略已於美股開市前20分鐘自動啟動！")
    run_backtest()
    with open(os.path.join(DATA_PATH, "capital_trend.json"), "r") as f:
        capital_trend = json.load(f)
    calc_performance(capital_trend)
    print("本次回測與績效計算已完成。")

def job_ai_summary():
    push_ai_learning_summary()
    print("AI學習摘要已推播。")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # 每天台灣時間 21:10 執行一次回測（美股夏令開盤前10分鐘）
    scheduler.add_job(job_backtest, 'cron', hour=21, minute=10)
    # 每天台灣時間 22:00 推播AI學習摘要
    scheduler.add_job(job_ai_summary, 'cron', hour=22, minute=0)
    print("排程啟動，等待自動回測與推播...（Ctrl+C 可中止）")
    # run_backtest()  # ← 已註解，僅靠排程自動執行
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("排程已中止。")
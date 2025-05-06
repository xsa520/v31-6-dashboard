import os
import json
import time
import pytz
from datetime import datetime
import requests

# Telegram 設定
BOT_TOKEN = "7088124949:AAFgfBGk9vr5csLetH-77EUdEZiRPV7NOJc"
CHAT_ID = "7398446407"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# 資料夾與狀態檔案位置
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATUS_PATH = os.path.join(DATA_DIR, "v31_status.json")

last_sent_time = None
last_trade_ids = set()

def send_telegram(text):
    try:
        payload = {"chat_id": CHAT_ID, "text": text}
        requests.post(TELEGRAM_URL, json=payload)
        print("✅ 推播成功")
    except Exception as e:
        print(f"❌ 推播失敗：{e}")

def check_and_notify():
    global last_sent_time, last_trade_ids

    try:
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            status = json.load(f)

        today_trades = status.get("today_trades", [])
        current_time = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")
        header = f"📢 [V31.9 策略通知] 台灣時間 {current_time}\n"

        current_ids = {f"{t['symbol']}_{t['time']}" for t in today_trades}

        if today_trades and current_ids != last_trade_ids:
            messages = []
            for trade in today_trades:
                messages.append(
                    f"操作：{trade['action']} {trade['symbol']}\n"
                    f"價格：${trade['price']}\n"
                    f"數量：{trade['quantity']} 股\n"
                    f"時間：{trade['time']}\n"
                )
            full_msg = header + "\n".join(messages)
            send_telegram(full_msg)
            last_trade_ids = current_ids

        elif not today_trades and (not last_sent_time or datetime.now().hour == 21):
            msg = header + "目前不進場：條件不足（MA150 / MACD / 量能）"
            send_telegram(msg)
            last_sent_time = datetime.now()

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    while True:
        check_and_notify()
        time.sleep(360)  # 每 6 分鐘檢查一次

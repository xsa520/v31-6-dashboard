import time
import json
import os
import requests
from datetime import datetime
import pytz

# Telegram Bot 設定
BOT_TOKEN = "7088124949:AAFgfBGk9vr5csLetH-77EUdEZiRPV7NOJc"
CHAT_ID = "7398446407"

# 資料夾路徑
DATA_DIR = os.path.join(os.path.dirname(__file__), "date")

# 設定時區
tz = pytz.timezone("America/New_York")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ 發送 Telegram 訊息失敗：{e}")

def check_strategy():
    try:
        status_path = os.path.join(DATA_DIR, "v31_status.json")
        with open(status_path, "r", encoding="utf-8") as f:
            status = json.load(f)
        # 檢查是否有策略訊號
        if status.get("action") in ["BUY", "SELL"]:
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            message = (
                f"[V31.9 策略通知]\n"
                f"操作：{status['action']} {status['symbol']}\n"
                f"金額：{status['amount']}\n"
                f"信心等級：{status['confidence']}\n"
                f"時間：{now}"
            )
            send_telegram_message(message)
    except Exception as e:
        print(f"❌ 檢查策略時發生錯誤：{e}")

def check_anomalies():
    try:
        anomalies_path = os.path.join(DATA_DIR, "anomalies.json")
        if os.path.exists(anomalies_path):
            with open(anomalies_path, "r", encoding="utf-8") as f:
                anomalies = json.load(f)
            if anomalies:
                now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                message = f"[異常監測通知]\n時間：{now}\n"
                for anomaly in anomalies:
                    message += f"- {anomaly}\n"
                send_telegram_message(message)
    except Exception as e:
        print(f"❌ 檢查異常時發生錯誤：{e}")

if __name__ == "__main__":
    print("✅ 背景工作者已啟動")
    while True:
        check_strategy()
        check_anomalies()
        time.sleep(60)  # 每分鐘檢查一次

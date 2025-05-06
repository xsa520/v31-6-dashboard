import os
import json
from datetime import datetime
import pytz
import requests

# 檔案路徑
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "v31_status.json")

# Telegram 設定
BOT_TOKEN = "7088124949:AAFgfBGk9vr5csLetH-77EUdEZiRPV7NOJc"
CHAT_ID = "7398446407"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(text):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": text
        }
        response = requests.post(TELEGRAM_URL, json=payload)
        response.raise_for_status()
        print("✅ 已發送推播")
    except Exception as e:
        print(f"❌ 推播失敗：{e}")

def update_status():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 時間處理
        la_time = datetime.now(pytz.timezone("America/Los_Angeles"))
        tw_time = datetime.now(pytz.timezone("Asia/Taipei"))

        la_str = la_time.strftime("%Y-%m-%d %H:%M:%S")
        tw_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

        data["last_update"] = la_str  # 寫入的是美西時間

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ 時間已更新為 美西：{la_str} / 台灣：{tw_str}")

        message = (
            "📊 V31.9 策略狀態更新成功\n"
            f"🇺🇸 美西時間：{la_str}\n"
            f"🇹🇼 台灣時間：{tw_str}\n"
            f"💰 資產：${data['capital']['current']}\n"
            f"📈 總損益：{data['capital']['profit']}（{data['capital']['profit_rate']}）"
        )
        send_telegram_message(message)

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    update_status()

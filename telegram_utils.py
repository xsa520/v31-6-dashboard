import requests

# 1. 策略/訊號推播用
TRADE_BOT_TOKEN = "7088124949:AAFgfBGk9vr5csLetH-77EUdEZiRPV7NOJc"
TRADE_CHAT_ID = "7398446407"

# 2. 系統異常/報表推播用
GUARDIAN_BOT_TOKEN = "8142937859:AAFIRhDThncqUSaYH4hYOUZcNLFFDMvaDQk"
GUARDIAN_CHAT_ID = "7398446407"

def send_trade_notify(message):
    """推播策略啟動、買賣訊號、牛熊警示等"""
    url = f"https://api.telegram.org/bot{TRADE_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TRADE_CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=data)
        return r.status_code == 200
    except Exception as e:
        print("推播失敗：", e)
        return False

def send_guardian_notify(message):
    """推播系統異常、定期報表、AI學習建議等"""
    url = f"https://api.telegram.org/bot{GUARDIAN_BOT_TOKEN}/sendMessage"
    data = {"chat_id": GUARDIAN_CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=data)
        return r.status_code == 200
    except Exception as e:
        print("推播失敗：", e)
        return False
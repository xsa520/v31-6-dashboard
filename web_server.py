from flask import Flask, render_template
import json
from datetime import datetime
import pytz
import os

app = Flask(__name__)

def load_json(filename, default={}):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 無法讀取 {filename}：{e}")
        return default

@app.route('/')
def index():
    # 路徑設定
    base_path = os.path.join(os.path.dirname(__file__), 'date')

    # 讀取各 JSON 檔案
    capital_trend = load_json(os.path.join(base_path, 'capital_trend.json'), default={})
    v31_status = load_json(os.path.join(base_path, 'v31_status.json'), default={})
    v31_status_history = load_json(os.path.join(base_path, 'v31_status_history.json'), default=[])
    anomalies = load_json(os.path.join(base_path, 'anomalies.json'), default=[])

    # 取得時間（台灣時區）
    tz = pytz.timezone('Asia/Taipei')
    now_time = datetime.now(tz).strftime('%Y/%m/%d 下午%I:%M:%S')

    # 若 capital_trend 是 list，強制轉為 dict 避免 keys() 出錯
    if isinstance(capital_trend, list):
        capital_trend = {}

    # 取最後一天總資金值
    total_capital = 0
    try:
        combined = capital_trend.get("綜合", [])
        if combined and isinstance(combined[-1], list) and len(combined[-1]) >= 2:
            total_capital = combined[-1][1]
    except Exception as e:
        print(f"⚠️ 讀取總資金錯誤: {e}")

    return render_template(
        'V31.6_Web_Dashboard.html',
        now_time=now_time,
        capital_trend=capital_trend,
        v31_status=v31_status,
        v31_status_history=v31_status_history,
        anomalies=anomalies,
        total_capital=total_capital
    )

if __name__ == '__main__':
    app.run(debug=True)

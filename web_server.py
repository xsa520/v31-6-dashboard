from flask import Flask, render_template
import json
from datetime import datetime
import pytz
import os

app = Flask(__name__)

def load_json(filename, default):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 無法讀取 {filename}：{e}")
        return default

@app.route('/')
def index():
    base_path = os.path.join(os.path.dirname(__file__), 'date')

    capital_trend = load_json(os.path.join(base_path, 'capital_trend.json'), {})
    v31_status = load_json(os.path.join(base_path, 'v31_status.json'), {})
    v31_status_history = load_json(os.path.join(base_path, 'v31_status_history.json'), [])
    anomalies = load_json(os.path.join(base_path, 'anomalies.json'), [])
    trade_records = load_json(os.path.join(base_path, 'trade_records.json'), [])

    # 確保格式為 dict
    if isinstance(capital_trend, list):
        capital_trend = {}

    # 台灣時間
    now = datetime.now(pytz.timezone('Asia/Taipei'))
    now_time = now.strftime('%Y/%m/%d %p%I:%M:%S')

    # 總資金計算
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
        trade_records=trade_records,
        total_capital=total_capital
    )

if __name__ == '__main__':
    app.run(debug=True)

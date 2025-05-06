from flask import Flask, render_template, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route('/')
def dashboard():
    status = load_json('v31_status.json')
    capital = status.get("capital", {})
    today_trades = status.get("today_trades", [])
    report = status.get("report", {})
    status_text = status.get("status", "⚠️ 無法讀取策略狀態")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template('dashboard.html',
                           now=now,
                           capital=capital,
                           today_trades=today_trades,
                           report=report,
                           status_text=status_text)

@app.route('/v31_status.json')
def get_status():
    return jsonify(load_json('v31_status.json'))

@app.route('/capital_trend.json')
def get_capital():
    return jsonify(load_json('capital_trend.json'))

@app.route('/v31_status_history.json')
def get_history():
    return jsonify(load_json('v31_status_history.json'))

if __name__ == '__main__':
    app.run(debug=True)

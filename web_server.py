from flask import Flask, render_template, jsonify
import json
from datetime import datetime
import pytz

app = Flask(__name__)

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

@app.route('/')
def index():
    status_data = load_json('date/v31_status.json')
    capital_trend_data = load_json('date/capital_trend.json')
    status_history_data = load_json('date/v31_status_history.json')

    # 時間顯示處理
    taiwan_time = datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S')
    us_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y/%m/%d %I:%M:%S %p')

    return render_template(
        'V31.6_Web_Dashboard.html',
        status=status_data,
        capital_trend=capital_trend_data,
        history=status_history_data,
        taiwan_time=taiwan_time,
        us_time=us_time
    )

@app.route('/api/status')
def get_status():
    return jsonify(load_json('date/v31_status.json'))

@app.route('/api/capital_trend')
def get_capital_trend():
    return jsonify(load_json('date/capital_trend.json'))

@app.route('/api/status_history')
def get_status_history():
    return jsonify(load_json('date/v31_status_history.json'))

if __name__ == '__main__':
    app.run(debug=True)

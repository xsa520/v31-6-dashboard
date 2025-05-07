from flask import Flask, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    try:
        with open("data/summary_metrics.json", "r") as f:
            summary_metrics = json.load(f)
    except:
        summary_metrics = {"annual_return": 0, "win_rate": 0, "risk_rate": 0, "capital": 0}

    try:
        with open("data/trade_records.json", "r") as f:
            trade_records = json.load(f)
    except:
        trade_records = []

    try:
        with open("data/anomalies.json", "r") as f:
            anomalies = json.load(f)
    except:
        anomalies = []

    try:
        with open("data/v31_status.json", "r") as f:
            v31_status = json.load(f)
    except:
        v31_status = {"status": "尚未評估", "recommendation": "無建議", "evaluate_time": "N/A"}

    return render_template(
        "V31.6_Web_Dashboard.html",
        summary_metrics=summary_metrics,
        trade_records=trade_records,
        anomalies=anomalies,
        v31_status=v31_status,
        current_time=datetime.now().strftime('%Y/%m/%d %p%I:%M:%S')
    )

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

def load_json(filename, default=None):
    filepath = os.path.join("data", filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}

@app.route("/")
def index():
    capital_trend = load_json("capital_trend.json", [])
    summary_metrics = load_json("summary_metrics.json", {
        "annual_return": 0, "win_rate": 0, "risk_rate": 0
    })
    v31_status = load_json("v31_status.json", {
        "status": "尚未評估", "suggestion": "無建議", "evaluated_at": "N/A"
    })
    trade_records = load_json("trade_records.json", [])
    anomalies = load_json("anomalies.json", [])

    return render_template(
        "V31.6_Web_Dashboard.html",
        capital_trend=capital_trend,
        summary_metrics=summary_metrics,
        v31_status=v31_status,
        trade_records=trade_records,
        anomalies=anomalies
    )

@app.route("/api/metrics")
def get_metrics():
    return jsonify(load_json("summary_metrics.json", {}))

@app.route("/api/trades")
def get_trades():
    return jsonify(load_json("trade_records.json", []))

@app.route("/api/status")
def get_status():
    return jsonify(load_json("v31_status.json", {}))

@app.route("/api/anomalies")
def get_anomalies():
    return jsonify(load_json("anomalies.json", []))

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template
import json
from datetime import datetime
import pytz

app = Flask(__name__)

def load_json(filepath, default):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

@app.route("/")
def index():
    taipei = pytz.timezone("Asia/Taipei")
    now_time = datetime.now(taipei).strftime("%Y/%m/%d %H:%M:%S")

    capital_trend_raw = load_json("date/capital_trend.json", [])
    v31_status = load_json("date/v31_status.json", {})
    v31_status_history = load_json("date/v31_status_history.json", {})
    anomalies = load_json("date/anomalies.json", [])

    return render_template(
        "V31.6_Web_Dashboard.html",
        now_time=now_time,
        capital_trend=capital_trend_raw,
        v31_status=v31_status,
        v31_status_history=v31_status_history,
        anomalies=anomalies
    )

if __name__ == "__main__":
    app.run(debug=True)

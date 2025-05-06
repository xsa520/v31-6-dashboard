from flask import Flask, render_template
import json
import os

app = Flask(__name__)

# 設定資料資料夾位置
DATA_DIR = os.path.join(os.path.dirname(__file__), "date")

@app.route("/")
def dashboard():
    # 讀取 v31_status.json
    with open(os.path.join(DATA_DIR, "v31_status.json"), "r", encoding="utf-8") as f:
        status = json.load(f)
    
    # 讀取 capital_trend.json
    with open(os.path.join(DATA_DIR, "capital_trend.json"), "r", encoding="utf-8") as f:
        capital_data = json.load(f)

    # 讀取 v31_status_history.json
    with open(os.path.join(DATA_DIR, "v31_status_history.json"), "r", encoding="utf-8") as f:
        history = json.load(f)

    return render_template(
        "dashboard.html",
        status=status,
        capital_data=capital_data,
        history=history
    )

if __name__ == "__main__":
    app.run(debug=True)


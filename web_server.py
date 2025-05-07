import os
from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
import requests
from datetime import datetime

app = Flask(__name__)

# === 環境變數讀取（Telegram Bot 設定） ===
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN", "8142937859:AAFIRhDThncqUSaYH4hYOUZcNLFFDMvaDQk")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID", "7398446407")

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, json=payload)
        return response.ok
    except Exception as e:
        print(f"❌ Telegram 錯誤: {e}")
        return False

# === 讀取資料 ===
def load_data():
    try:
        df = pd.read_csv("data/summary_metrics.csv")
        trades = pd.read_csv("data/trade_history.csv")
        latest_status = pd.read_csv("data/latest_strategy_status.csv")
        return df, trades, latest_status
    except Exception as e:
        print(f"❌ 資料讀取失敗: {e}")
        return None, None, None

# === 曲線圖 ===
def create_equity_curve(trades):
    try:
        trades["date"] = pd.to_datetime(trades["date"])
        trades = trades.sort_values("date")
        trades["equity"] = trades["capital"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trades["date"], y=trades["equity"], mode='lines+markers', name='資產淨值'))
        fig.update_layout(title="💰 資產淨值走勢圖", xaxis_title="日期", yaxis_title="累積資本")
        return fig.to_html(full_html=False)
    except Exception as e:
        print(f"❌ 曲線圖錯誤: {e}")
        return "<p>⚠️ 資產曲線圖載入失敗</p>"

@app.route("/")
def index():
    df, trades, latest_status = load_data()

    if df is None or trades is None or latest_status is None:
        send_telegram_message("❌ Dashboard 資料讀取失敗，請立即檢查部署狀況")
        return "<h3>❌ Dashboard 資料讀取失敗</h3>"

    try:
        metrics = df.iloc[0]
        summary_metrics = {
            "total_capital": f"${metrics['total_capital']:.2f}",
            "annual_return": f"{metrics['annual_return']:.2f}",
            "win_rate": f"{metrics['win_rate']:.2f}",
            "risk": f"{metrics['risk']:.2f}",
        }

        trade_table = trades.tail(20).to_dict(orient="records")

        strategy_status = {
            "current_strategy": latest_status["strategy"].values[0],
            "suggestion": latest_status["suggestion"].values[0],
            "timestamp": latest_status["timestamp"].values[0],
        }

        equity_chart = create_equity_curve(trades)

        return render_template(
            "V31.6_Web_Dashboard.html",
            summary_metrics=summary_metrics,
            trade_table=trade_table,
            strategy_status=strategy_status,
            equity_chart=equity_chart
        )

    except Exception as e:
        print(f"❌ 頁面渲染錯誤: {e}")
        send_telegram_message(f"❌ Dashboard 渲染錯誤：{e}")
        return "<h3>❌ 頁面渲染錯誤</h3>"

if __name__ == "__main__":
    app.run(debug=True)

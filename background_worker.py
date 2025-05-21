from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
import os

# 匯入 run_backtest_v38 主要功能
from run_backtest_v38 import run_backtest, calc_performance, push_ai_learning_summary, DATA_PATH

def run_v38_and_report():
    print("V38 background worker 啟動！", datetime.now())
    # 清除舊資料
    if os.path.exists(os.path.join(DATA_PATH, "capital_trend.json")):
        os.remove(os.path.join(DATA_PATH, "capital_trend.json"))
    if os.path.exists(os.path.join(DATA_PATH, "trade_records.json")):
        os.remove(os.path.join(DATA_PATH, "trade_records.json"))
    if os.path.exists(os.path.join(DATA_PATH, "ai_learn_log.json")):
        os.remove(os.path.join(DATA_PATH, "ai_learn_log.json"))

    # 執行策略
    run_backtest()
    # 計算績效
    import json
    with open(os.path.join(DATA_PATH, "capital_trend.json"), "r") as f:
        capital_trend = json.load(f)
    calc_performance(capital_trend)
    # 推播AI學習摘要
    push_ai_learning_summary()
    print("V38 background worker 執行完畢！", datetime.now())

if __name__ == '__main__':
    scheduler = BlockingScheduler(timezone=pytz.timezone('America/New_York'))
    # 美股開盤 9:30，提前 20 分鐘是 9:10
    scheduler.add_job(run_v38_and_report, 'cron', day_of_week='mon-fri', hour=9, minute=10)
    print("背景排程啟動，等待美股開市前20分鐘自動執行...")
    scheduler.start()
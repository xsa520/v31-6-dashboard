import os
import pandas as pd
from backtest import run_backtest

def batch_backtest(folder_path, strategy_params):
    results = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            stock_name = filename.replace('.csv', '')
            df = pd.read_csv(os.path.join(folder_path, filename), parse_dates=['Date'])
            df = df.sort_values('Date')
            # 新增：將 Date 設為 index
            df = df.set_index('Date')
            # 強制將 Close 和 Volume 轉為數值型態，並去除缺失值
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df = df.dropna(subset=['Close', 'Volume'])
            backtest_result = run_backtest(df, strategy_params)
            result = backtest_result.iloc[0].to_dict()
            result['Stock'] = stock_name
            results.append(result)
    report = pd.DataFrame(results)
    return report

if __name__ == '__main__':
    strategy_params = {'ma_short': 5, 'ma_long': 20}
    folder_path = './stock_data'
    report = batch_backtest(folder_path, strategy_params)
    print(report)
    report.to_csv('batch_backtest_report.csv', index=False)
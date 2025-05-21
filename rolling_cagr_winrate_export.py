import pandas as pd
import numpy as np
import os

def calc_rolling_cagr_and_winrate(df, window=252):
    rolling_cagr = []
    rolling_winrate = []
    dates = []
    for i in range(len(df) - window + 1):
        sub_df = df.iloc[i:i+window]
        start_price = sub_df['Close'].iloc[0]
        end_price = sub_df['Close'].iloc[-1]
        n_years = (sub_df.index[-1] - sub_df.index[0]).days / 365.25
        if start_price > 0 and n_years > 0:
            cagr = (end_price / start_price) ** (1 / n_years) - 1
            winrate = (sub_df['Close'].pct_change() > 0).sum() / (window-1)
            rolling_cagr.append(cagr)
            rolling_winrate.append(winrate)
            dates.append(sub_df.index[-1])
    return rolling_cagr, rolling_winrate, dates

folder_path = './stock_data'
window = 252  # 1年

summary = []

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        stock_name = filename.replace('.csv', '')
        df = pd.read_csv(os.path.join(folder_path, filename), parse_dates=['Date'])
        df = df.set_index('Date')
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df.dropna(subset=['Close'])
        rolling_cagr, rolling_winrate, dates = calc_rolling_cagr_and_winrate(df, window)
        if len(rolling_cagr) == 0:
            continue
        final_cagr = rolling_cagr[-1]
        final_winrate = rolling_winrate[-1]
        avg_cagr = np.mean(rolling_cagr)
        avg_winrate = np.mean(rolling_winrate)
        for d, c, w in zip(dates, rolling_cagr, rolling_winrate):
            summary.append({
                'Stock': stock_name,
                'Date': d,
                'Rolling_CAGR': c,
                'Rolling_WinRate': w,
                'Final_CAGR': final_cagr,
                'Final_WinRate': final_winrate,
                'Avg_CAGR': avg_cagr,
                'Avg_WinRate': avg_winrate
            })

summary_df = pd.DataFrame(summary)
print('summary_df 長度:', len(summary_df))
print(summary_df.head())
summary_df.to_csv('all_stocks_rolling_cagr_winrate.csv', index=False)
print('已存成 all_stocks_rolling_cagr_winrate.csv')

# 如果只要每檔股票一行的最終/平均績效
final_summary = summary_df.groupby('Stock').agg({
    'Final_CAGR': 'last',
    'Final_WinRate': 'last',
    'Avg_CAGR': 'last',
    'Avg_WinRate': 'last'
}).reset_index()
final_summary.to_csv('all_stocks_final_avg_cagr_winrate.csv', index=False)
print('已存成 all_stocks_final_avg_cagr_winrate.csv')
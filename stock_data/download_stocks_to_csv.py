import yfinance as yf
import os
import numpy as np
import pandas as pd

def is_stock_suitable(stock_data):
    # 1. 高波動性（年化波動率 > 30%）
    daily_ret = stock_data['Close'].pct_change().dropna()
    ann_vol = float(daily_ret.std() * np.sqrt(252))
    if ann_vol <= 0.3:
        return False

    # 2. 有明顯趨勢（過去200日MA與當前股價斜率為正）
    if len(stock_data) < 200:
        return False
    ma200 = stock_data['Close'].rolling(200).mean()
    y = ma200[-200:].dropna().values
    x = np.arange(len(y))
    if len(y) < 2:
        return False
    slope = np.polyfit(x, y, 1)[0]
    if slope <= 0:
        return False

    # 3. 有足夠流動性（平均日交易量 > 100萬股）
    avg_vol = stock_data['Volume'].tail(252).mean()
    if avg_vol <= 1_000_000:
        return False

    # 4. 價格在近一年內有出現超過 ±40% 的漲跌幅
    close_1y = stock_data['Close'].tail(252)
    max_return = (close_1y.max() - close_1y.min()) / close_1y.min()
    if max_return < 0.4:
        return False

    return True

symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'BIDU', 'ADBE']
folder_path = './stock_data'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
suitable_stocks = []

for symbol in symbols:
    df = yf.download(symbol, start='2010-01-01', end='2023-12-31')
    if not df.empty:
        df = df[['Close', 'Volume']].dropna()
        df = df.reset_index()  # 讓 Date 變成欄位
        if is_stock_suitable(df):
            df.to_csv(f'{folder_path}/{symbol}.csv', index=False)
            suitable_stocks.append(symbol)
            print(f'{symbol} 通過篩選，已儲存')
        else:
            print(f'{symbol} 未通過篩選')
    else:
        print(f'{symbol} 沒有資料')

print('通過篩選的股票：', suitable_stocks)
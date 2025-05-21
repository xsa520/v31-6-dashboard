import yfinance as yf
import os
import pandas as pd
from is_stock_suitable import is_stock_suitable

symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'BIDU', 'ADBE']
folder_path = './stock_data'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

for symbol in symbols:
    df = yf.download(symbol, start='2010-01-01', end='2023-12-31')
    if not df.empty:
        df = df[['Close', 'Volume']].dropna().reset_index()
        if is_stock_suitable(df):
            df.to_csv(f'{folder_path}/{symbol}.csv', index=False)
            print(f'{symbol} 通過篩選，已儲存')
        else:
            print(f'{symbol} 未通過篩選')
    else:
        print(f'{symbol} 沒有資料')
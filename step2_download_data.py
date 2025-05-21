import pandas as pd
import yfinance as yf

# 股票清單
symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META']  # 你可以自行增減

# 下載所有股票的資料
price_data_dict = {}
for symbol in symbols:
    data = yf.download(symbol, start='2010-01-01', end='2023-12-31')[['Close']].dropna()
    data.index = pd.to_datetime(data.index)
    price_data_dict[symbol] = data
    print(f"{symbol} 資料前5筆：")
    print(data.head())

# 初始參數
strategy_params = {'ma_short': 5, 'ma_long': 20}
print(strategy_params)
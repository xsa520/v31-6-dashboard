import numpy as np

def is_stock_suitable(stock_data):
    """
    判斷股票是否適合本策略
    stock_data: DataFrame，需有 'Close', 'Volume', 'Date' 欄位
    回傳 True/False
    """
    # 1. 高波動性（年化波動率 > 30%）
    daily_ret = stock_data['Close'].pct_change().dropna()
    ann_vol = daily_ret.std() * np.sqrt(252)
    if ann_vol <= 0.3:
        return False

    # 2. 有明顯趨勢（過去200日MA與當前股價斜率為正）
    if len(stock_data) < 200:
        return False
    ma200 = stock_data['Close'].rolling(200).mean()
    # 用線性回歸計算200日MA斜率
    y = ma200[-200:].dropna().values
    x = np.arange(len(y))
    if len(y) < 2:
        return False
    slope = np.polyfit(x, y, 1)[0]
    if slope <= 0:
        return False

    # 3. 有足夠流動性（平均日交易量 > 100萬股）
    avg_vol = stock_data['Volume'].tail(252).mean()  # 近一年
    if avg_vol <= 1_000_000:
        return False

    # 4. 價格在近一年內有出現超過 ±40% 的漲跌幅
    close_1y = stock_data['Close'].tail(252)
    max_return = (close_1y.max() - close_1y.min()) / close_1y.min()
    if max_return < 0.4:
        return False

    return True
def to_float(x):
    import numpy as np
    import pandas as pd
    if isinstance(x, pd.Series) or isinstance(x, np.ndarray):
        if hasattr(x, 'iloc') and x.size == 1:
            return float(x.iloc[0])
        return float(np.ravel(x)[-1])
    return float(x)

def is_bull_market(ma150, ma50):
    # 強制轉 float，避免 Series 比較錯誤
    return float(ma50) > float(ma150)

def is_bear_market(ma150, ma50):
    # 強制轉 float，避免 Series 比較錯誤
    return float(ma50) < float(ma150)
def evaluate_buy(price, ma50, ma150, macd, volume, avg_volume, prev_high, rsi):
    price = to_float(price)
    ma50 = to_float(ma50)
    ma150 = to_float(ma150)
    macd = to_float(macd)
    volume = to_float(volume)
    avg_volume = to_float(avg_volume)
    prev_high = to_float(prev_high)
    rsi = to_float(rsi)
    return (
        (ma50 > ma150) and
        (macd > 0) and
        (rsi > 51) and
        (price > prev_high) and
        (volume > avg_volume * 1.2)
    )

def evaluate_sell(entry_price, current_price, max_profit, macd_hist, volume, avg_volume, support):
    entry_price = to_float(entry_price)
    current_price = to_float(current_price)
    max_profit = to_float(max_profit)
    macd_hist = to_float(macd_hist)
    volume = to_float(volume)
    avg_volume = to_float(avg_volume)
    support = to_float(support)
    profit_ratio = (current_price - entry_price) / entry_price
    if profit_ratio <= -0.10:
        return "SELL_STOP_LOSS"
    if profit_ratio >= 0.65 and (macd_hist < 0 or volume < avg_volume * 0.5):
        return "SELL_TAKE_PROFIT"
    if profit_ratio >= 0.15 and max_profit - profit_ratio >= 0.10:
        return "SELL_TRAILING_STOP"
    if current_price < support:
        return "SELL_FAKE_BREAK"
    return "HOLD"
def evaluate_short_sell(price, ma50, ma150, macd, volume, avg_volume, prev_low, rsi):
    price = to_float(price)
    ma50 = to_float(ma50)
    ma150 = to_float(ma150)
    macd = to_float(macd)
    volume = to_float(volume)
    avg_volume = to_float(avg_volume)
    prev_low = to_float(prev_low)
    rsi = to_float(rsi)
    return (
        (ma50 < ma150) and
        (macd < 0) and
        (rsi < 47) and
        (price < prev_low) and
        (volume > avg_volume * 1.2)
    )

def evaluate_short_cover(entry_price, current_price, max_profit, macd_hist, volume, avg_volume, resistance):
    entry_price = to_float(entry_price)
    current_price = to_float(current_price)
    max_profit = to_float(max_profit)
    macd_hist = to_float(macd_hist)
    volume = to_float(volume)
    avg_volume = to_float(avg_volume)
    resistance = to_float(resistance)
    profit_ratio = (entry_price - current_price) / entry_price
    if profit_ratio <= -0.10:
        return "COVER_STOP_LOSS"
    if profit_ratio >= 0.65 and (macd_hist > 0 or volume < avg_volume * 0.5):
        return "COVER_TAKE_PROFIT"
    if profit_ratio >= 0.15 and max_profit - profit_ratio >= 0.10:
        return "COVER_TRAILING_STOP"
    if current_price > resistance:
        return "COVER_FAKE_BREAK"
    return "HOLD"
def dynamic_stock_selection():
    return ["NVDA", "TSLA", "AAPL"]

def get_selected_pool():
    return ["NVDA", "PLTR", "CELH", "AAPL"]
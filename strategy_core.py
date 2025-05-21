def is_bull_market(ma150_series, ma50_series):
    return ma50_series[-1] > ma150_series[-1]

def is_bear_market(ma150_series, ma50_series):
    return ma50_series[-1] < ma150_series[-1]

def evaluate_buy(price, ma50, ma150, macd, volume, avg_volume, prev_high, rsi):
    # 量能過濾 avg_volume*1.2，RSI>51
    return (
        ma50 > ma150 and
        macd > 0 and
        rsi > 51 and
        price > prev_high and
        volume > avg_volume * 1.2
    )

def evaluate_sell(entry_price, current_price, max_profit, macd_hist, volume, avg_volume, support):
    profit_ratio = (current_price - entry_price) / entry_price
    # 止損10%，停利65%，移動停損10%，MACD翻負、量能急縮、跌破支撐
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
    # 量能過濾 avg_volume*1.2，RSI<47
    return (
        ma50 < ma150 and
        macd < 0 and
        rsi < 47 and
        price < prev_low and
        volume > avg_volume * 1.2
    )

def evaluate_short_cover(entry_price, current_price, max_profit, macd_hist, volume, avg_volume, resistance):
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

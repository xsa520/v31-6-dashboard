import numpy as np

# 假設策略參數是一個 dict，例如 {'ma_short': 5, 'ma_long': 20}
def optimize_strategy(train_data, strategy_params):
    """
    在訓練資料上尋找最佳策略參數
    這裡以簡單範例：遍歷短期/長期均線組合，選擇CAGR最高者
    """
    best_params = strategy_params.copy()
    best_cagr = -np.inf
    # 範例：短期均線 5~20，長期均線 21~60
    for ma_short in range(5, 21):
        for ma_long in range(ma_short+1, 61):
            params = strategy_params.copy()
            params['ma_short'] = ma_short
            params['ma_long'] = ma_long
            cagr = evaluate_ma_cagr(train_data, params)
            if cagr > best_cagr:
                best_cagr = cagr
                best_params = params.copy()
    return best_params

def evaluate_ma_cagr(data, params):
    """
    用移動平均交叉策略計算 CAGR（僅作為範例）
    """
    ma_short = data['Close'].rolling(params['ma_short']).mean()
    ma_long = data['Close'].rolling(params['ma_long']).mean()
    signal = (ma_short > ma_long).astype(int)
    signal = signal.shift(1).fillna(0)
    ret = data['Close'].pct_change().fillna(0)
    strat_ret = ret * signal
    cum_ret = (1 + strat_ret).cumprod()
    n_years = (data.index[-1] - data.index[0]).days / 365.25
    if n_years <= 0:
        return 0
    cagr = cum_ret.iloc[-1] ** (1/n_years) - 1
    return cagr
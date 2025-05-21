from is_stock_suitable import is_stock_suitable
import pandas as pd

def run_backtest(test_data, strategy_params):
    if not is_stock_suitable(test_data):
        return pd.DataFrame([{
            'CAGR': None,
            'Max Drawdown': None,
            'Win Rate': None,
            'Trades': None,
            'Remark': 'Unsuitable for strategy'
        }])
    ma_short = test_data['Close'].rolling(strategy_params['ma_short']).mean()
    ma_long = test_data['Close'].rolling(strategy_params['ma_long']).mean()
    signal = (ma_short > ma_long).astype(int)
    signal = signal.shift(1).fillna(0)
    ret = test_data['Close'].pct_change().fillna(0)
    strat_ret = ret * signal
    cum_ret = (1 + strat_ret).cumprod()
    n_years = (test_data.index[-1] - test_data.index[0]).days / 365.25
    cagr = cum_ret.iloc[-1] ** (1/n_years) - 1 if n_years > 0 else 0
    cum_max = cum_ret.cummax()
    drawdown = (cum_ret - cum_max) / cum_max
    max_drawdown = drawdown.min()
    win_rate = (strat_ret > 0).sum() / (strat_ret != 0).sum() if (strat_ret != 0).sum() > 0 else 0
    trades = (signal.diff().abs() == 1).sum()
    return pd.DataFrame([{
        'CAGR': cagr,
        'Max Drawdown': max_drawdown,
        'Win Rate': win_rate,
        'Trades': trades,
        'Remark': 'OK'
    }])
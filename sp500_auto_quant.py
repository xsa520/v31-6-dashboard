import pandas as pd
import yfinance as yf
import os

def get_sp500_symbols():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    df = table[0]
    symbols = df['Symbol'].tolist()
    symbols = [s.replace('.', '-') for s in symbols]
    return symbols

def download_sp500_data(symbols, folder_path='./sp500_data'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    for symbol in symbols:
        try:
            df = yf.download(symbol, start='2010-01-01', end='2023-12-31')
            if not df.empty:
                df = df[['Close', 'Volume']].dropna().reset_index()
                df.to_csv(f'{folder_path}/{symbol}.csv', index=False)
                print(f'{symbol} 已儲存')
            else:
                print(f'{symbol} 無資料')
        except Exception as e:
            print(f'{symbol} 下載失敗: {e}')
import numpy as np

def run_backtest(df, strategy_params):
    ma_short = df['Close'].rolling(strategy_params['ma_short']).mean()
    ma_long = df['Close'].rolling(strategy_params['ma_long']).mean()
    signal = (ma_short > ma_long).astype(int)
    signal = signal.shift(1).fillna(0)
    ret = df['Close'].pct_change().fillna(0)
    strat_ret = ret * signal
    cum_ret = (1 + strat_ret).cumprod()
    n_years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = cum_ret.iloc[-1] ** (1/n_years) - 1 if n_years > 0 else 0
    win_rate = (strat_ret > 0).sum() / (strat_ret != 0).sum() if (strat_ret != 0).sum() > 0 else 0
    cum_max = cum_ret.cummax()
    drawdown = (cum_ret - cum_max) / cum_max
    max_drawdown = drawdown.min()
    return cagr, win_rate, max_drawdown
def batch_backtest(folder_path, strategy_params):
    results = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            stock_name = filename.replace('.csv', '')
            df = pd.read_csv(os.path.join(folder_path, filename), parse_dates=['Date'])
            df = df.set_index('Date')
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df = df.dropna(subset=['Close'])
            if len(df) < 252*3:  # 至少三年資料
                continue
            cagr, win_rate, max_drawdown = run_backtest(df, strategy_params)
            results.append({
                'Stock': stock_name,
                'CAGR': cagr,
                'WinRate': win_rate,
                'MaxDrawdown': max_drawdown
            })
    report = pd.DataFrame(results)
    return report
def optimize_params(folder_path):
    best_params = None
    best_avg_cagr = -999
    for ma_short in range(5, 21, 5):
        for ma_long in range(ma_short+5, 61, 5):
            strategy_params = {'ma_short': ma_short, 'ma_long': ma_long}
            report = batch_backtest(folder_path, strategy_params)
            avg_cagr = report['CAGR'].mean()
            print(f'參數: {strategy_params}, 平均CAGR: {avg_cagr:.4f}')
            if avg_cagr > best_avg_cagr:
                best_avg_cagr = avg_cagr
                best_params = strategy_params
    print('最佳參數:', best_params)
    print('最佳平均CAGR:', best_avg_cagr)
    return best_params, best_avg_cagr
if __name__ == '__main__':
    print('取得S&P500成分股...')
    symbols = get_sp500_symbols()
    print(f'共{len(symbols)}檔')

    print('下載S&P500歷史資料...')
    download_sp500_data(symbols, folder_path='./sp500_data')

    print('開始自動化參數優化...')
    best_params, best_avg_cagr = optimize_params('./sp500_data')

    print('用最佳參數回測全市場...')
    final_report = batch_backtest('./sp500_data', best_params)
    final_report.to_csv('sp500_final_report.csv', index=False)
    print('已存成 sp500_final_report.csv')

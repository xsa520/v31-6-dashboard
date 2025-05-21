from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import os

def calc_cagr(start_value, end_value, n_years):
    if start_value <= 0 or n_years <= 0:
        return 0
    return (end_value / start_value) ** (1 / n_years) - 1

app = Flask(__name__)

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('V31.6_Web_Dashboard.html')

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    # 1. 讀取資產歷史
    try:
        account_history = pd.read_csv('account_history.csv', parse_dates=['date'])
    except:
        account_history = pd.DataFrame(columns=['date', 'asset'])
    # 2. 讀取交易紀錄
    try:
        trade_records = pd.read_csv('trade_records.csv')
    except:
        trade_records = pd.DataFrame(columns=['date', 'ticker', 'action', 'price', 'shares'])
    # 3. 取得所有有交易的股票
    tickers = sorted(trade_records['ticker'].unique()) if not trade_records.empty else []
    # 4. 下拉選單選擇股票
    selected_ticker = request.args.get('ticker', tickers[0] if tickers else None)
    # 5. 單股績效資料
    if selected_ticker:
        stock_trades = trade_records[trade_records['ticker'] == selected_ticker]
        try:
            stock_price = pd.read_csv(f'./sp500_data/{selected_ticker}.csv', parse_dates=['Date'])
            stock_price = stock_price.set_index('Date')
        except:
            stock_price = pd.DataFrame()
        if not stock_price.empty:
            start_price = stock_price['Close'].iloc[0]
            end_price = stock_price['Close'].iloc[-1]
            n_years = (stock_price.index[-1] - stock_price.index[0]).days / 365.25
            stock_cagr = calc_cagr(start_price, end_price, n_years)
        else:
            stock_cagr = 0
    else:
        stock_trades = pd.DataFrame()
        stock_price = pd.DataFrame()
        stock_cagr = 0
    if not account_history.empty:
        initial_asset = account_history['asset'].iloc[0]
        final_asset = account_history['asset'].iloc[-1]
        n_years = (account_history['date'].iloc[-1] - account_history['date'].iloc[0]).days / 365.25
        total_cagr = calc_cagr(initial_asset, final_asset, n_years)
    else:
        initial_asset = final_asset = total_cagr = 0
    if not trade_records.empty:
        win_trades = trade_records[(trade_records['action'] == '賣出') & (trade_records['price'] > 0)]
        win_rate = f"{(win_trades['price'] > 0).mean() * 100:.1f}%"
    else:
        win_rate = "0%"
    if not account_history.empty:
        cummax = account_history['asset'].cummax()
        drawdown = (account_history['asset'] - cummax) / cummax
        max_drawdown = f"{drawdown.min() * 100:.2f}%"
    else:
        max_drawdown = "0%"
    return jsonify({
        'account_history': account_history.to_dict('records'),
        'trade_records': trade_records.to_dict('records'),
        'tickers': tickers,
        'selected_ticker': selected_ticker,
        'stock_trades': stock_trades.to_dict('records'),
        'stock_price': stock_price.reset_index().to_dict('records') if not stock_price.empty else [],
        'stock_cagr': f"{stock_cagr*100:.2f}%",
        'initial_asset': initial_asset,
        'final_asset': final_asset,
        'total_cagr': f"{total_cagr*100:.2f}%",
        'win_rate': win_rate,
        'max_drawdown': max_drawdown
    })

if __name__ == '__main__':
    app.run(debug=True) 
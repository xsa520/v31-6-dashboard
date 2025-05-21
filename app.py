import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('V31.6_Web_Dashboard.html')

@app.route('/api/dashboard')
def api_dashboard():
    # 讀取績效摘要
    try:
        with open(os.path.join('data', 'performance_summary.json'), 'r') as f:
            perf = json.load(f)
    except Exception as e:
        print("讀取績效摘要錯誤：", e)
        perf = {
            'initial_capital': 10000,
            'final_capital': 10000,
            'cagr': 0,
            'win_rate': 0,
            'max_drawdown': 0
        }

    # 讀取資產歷史
    try:
        account_df = pd.read_csv(os.path.join('data', 'account_history.csv'))
        account_history = [
            {'date': str(row['date']), 'asset': row['capital']}
            for _, row in account_df.iterrows()
        ]
    except Exception as e:
        print("讀取 account_history.csv 錯誤：", e)
        account_history = []

    # 讀取交易紀錄
    try:
        trade_df = pd.read_csv(os.path.join('data', 'trade_records.csv'))
        trade_records = trade_df.to_dict(orient='records')
    except Exception as e:
        print("讀取 trade_records.csv 錯誤：", e)
        trade_records = []
    # 單股績效與下拉選單
    tickers = sorted(list(set([t['ticker'] for t in trade_records]))) if trade_records else []
    selected_ticker = request.args.get('ticker') or (tickers[0] if tickers else '')
    stock_cagr = "0.00%"

    # 單股績效曲線
    stock_price = []
    if 'account_df' in locals() and selected_ticker and 'symbol' in account_df.columns:
        try:
            stock_df = account_df[account_df['symbol'] == selected_ticker]
            stock_price = [
                {'Date': str(row['date']), 'Close': row['capital']}
                for _, row in stock_df.iterrows()
            ]
        except Exception as e:
            print("單股績效曲線錯誤：", e)
            stock_price = []

    # 回傳 JSON 給前端
    return jsonify({
        'initial_asset': f"${perf['initial_capital']:,.2f}",
        'final_asset': f"${perf['final_capital']:,.2f}",
        'total_cagr': f"{perf['cagr']:.2%}",
        'win_rate': f"{perf['win_rate']:.2%}",
        'max_drawdown': f"{perf['max_drawdown']:.2%}",
        'account_history': account_history,
        'trade_records': trade_records,
        'tickers': tickers,
        'selected_ticker': selected_ticker,
        'stock_cagr': stock_cagr,
        'stock_price': stock_price
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
import os
import pandas as pd
import numpy as np
import datetime
import time
import requests
from is_stock_suitable import is_stock_suitable

def is_rebalance_day():
    today = datetime.date.today()
    return today.day == 1

def send_telegram(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        resp = requests.post(url, data=payload)
        if resp.status_code == 200:
            print("已發送Telegram通知")
        else:
            print("Telegram通知失敗:", resp.text)
    except Exception as e:
        print("Telegram通知發生錯誤:", e)
def calc_fund_flow_strength(df):
    avg_vol_60 = float(df['Volume'].tail(60).mean())
    avg_vol_252 = float(df['Volume'].tail(252).mean())
    if avg_vol_252 == 0:
        return 0
    return avg_vol_60 / avg_vol_252

def calc_score(cagr, winrate, sharpe, max_drawdown, fund_flow_strength):
    return (cagr * 0.3) + (winrate * 0.15) + (sharpe * 0.2) - (abs(max_drawdown) * 0.1) + (fund_flow_strength * 0.25)

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
    return cagr, win_rate, max_drawdown, strat_ret

def assign_weights(df, max_weight=0.3):
    total_score = df['Score'].sum()
    df['RawWeight'] = df['Score'] / total_score
    df['Weight'] = df['RawWeight'].apply(lambda x: min(x, max_weight))
    df['Weight'] = df['Weight'] / df['Weight'].sum()
    return df

def place_order(stock, weight, action, api_client):
    print(f"下單: {action} {stock} 權重: {weight}")
    # 這裡串接FUTO API
    # api_client.place_order(stock, weight, action)
def adjust_weight_by_score_change(current_df, last_df, threshold=0.3):
    # 根據分數變化自動調整權重或剔除
    adjusted = []
    for idx, row in current_df.iterrows():
        stock = row['Stock']
        score = row['Score']
        last_score = last_df[last_df['Stock'] == stock]['Score'].values
        if len(last_score) > 0:
            last_score = last_score[0]
            if last_score > 0 and (score < last_score * (1 - threshold)):
                # 分數大幅下降，權重減半
                row['Weight'] = row['Weight'] * 0.5
                # 或直接 continue 跳過這檔
        adjusted.append(row)
    return pd.DataFrame(adjusted)
def main():
    log_file = "rebalance_log.txt"
    score_history_file = "score_history.csv"
    bot_token = "8142937859:AAFIRhDThncqUSaYH4hYOUZcNLFFDMvaDQk"
    chat_id = "7398446407"
    api_client = None  # FUTO API物件

    while True:
        try:
            if is_rebalance_day():
                with open(log_file, "a") as log:
                    log.write(f"{datetime.datetime.now()} - 執行再平衡\n")
                # 1. 建立 Universe
                universe = []
                for filename in os.listdir('./sp500_data'):
                    if filename.endswith('.csv'):
                        df = pd.read_csv(os.path.join('./sp500_data', filename), parse_dates=['Date'])
                        df = df.set_index('Date')
                        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
                        df = df.dropna(subset=['Close', 'Volume'])
                        if is_stock_suitable(df):
                            universe.append(filename.replace('.csv', ''))
                # 2. 精選候選池打分
                candidates = []
                for stock in universe:
                    df = pd.read_csv(f'./sp500_data/{stock}.csv', parse_dates=['Date'])
                    df = df.set_index('Date')
                    if len(df) == 0:
                        continue
                    recent_start = df.index.max() - pd.Timedelta(days=180)
                    df_recent = df.loc[df.index >= recent_start].copy()
                    df_recent['Close'] = pd.to_numeric(df_recent['Close'], errors='coerce')
                    df_recent['Volume'] = pd.to_numeric(df_recent['Volume'], errors='coerce')
                    df_recent = df_recent.dropna(subset=['Close', 'Volume'])
                    if len(df_recent) < 60:
                        continue
                    cagr, winrate, max_drawdown, strat_ret = run_backtest(df_recent, {'ma_short': 10, 'ma_long': 15})
                    sharpe = strat_ret.mean() / strat_ret.std() * np.sqrt(252) if strat_ret.std() > 0 else 0
                    fund_flow_strength = calc_fund_flow_strength(df_recent)
                    score = calc_score(cagr, winrate, sharpe, max_drawdown, fund_flow_strength)
                    candidates.append({
                        'Stock': stock,
                        'CAGR': cagr,
                        'WinRate': winrate,
                        'Sharpe': sharpe,
                        'MaxDrawdown': max_drawdown,
                        'FundFlowStrength': fund_flow_strength,
                        'Score': score
                    })
                candidates_df = pd.DataFrame(candidates)
                candidates_df = candidates_df.sort_values('Score', ascending=False)
                # 3. 自動選股/建倉與權重分配
                N = 10
                max_weight = 0.3
                selected = assign_weights(candidates_df.head(N), max_weight=max_weight)
                # 4. 分數歷史調整
                if os.path.exists(score_history_file):
                    last_scores = pd.read_csv(score_history_file)
                    selected = adjust_weight_by_score_change(selected, last_scores, threshold=0.3)
                # 5. API自動下單
                for _, row in selected.iterrows():
                    place_order(row['Stock'], row['Weight'], 'buy', api_client)
                selected.to_csv('selected_stock_pool.csv', index=False)
                # 6. 存分數歷史
                selected[['Stock', 'Score']].to_csv(score_history_file, index=False)
                # 7. 通知
                msg = f"再平衡已完成\n本次建倉池：\n{selected[['Stock','Weight']].to_string()}"
                send_telegram(msg, bot_token, chat_id)
                print("已完成本次再平衡，休息一天")
                time.sleep(86400)
            else:
                print("不是再平衡日，休息一小時")
                time.sleep(3600)
        except Exception as e:
            with open(log_file, "a") as log:
                log.write(f"{datetime.datetime.now()} - 發生錯誤: {e}\n")
            send_telegram(f"再平衡系統發生錯誤: {e}", bot_token, chat_id)
            print("發生錯誤:", e)
            time.sleep(600)

if __name__ == '__main__':
    main()
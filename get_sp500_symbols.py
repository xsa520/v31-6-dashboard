import pandas as pd

def get_sp500_symbols():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    df = table[0]
    symbols = df['Symbol'].tolist()
    # Yahoo Finance 有些股票代碼有「.」要換成「-」
    symbols = [s.replace('.', '-') for s in symbols]
    return symbols

if __name__ == '__main__':
    sp500_symbols = get_sp500_symbols()
    print('S&P500成分股數量:', len(sp500_symbols))
    print('前10檔:', sp500_symbols[:10])
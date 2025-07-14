# yfinanceからデータを取得するモジュール
import yfinance as yf
import pandas as pd

def fetch_all_price_data(ticker_list, benchmark_ticker):
    """全銘柄とベンチマークの株価データを一括で取得"""
    print("Fetching price data from yfinance...")
    all_tickers_to_fetch = ticker_list + [benchmark_ticker]
    hist_prices_all = yf.download(
        all_tickers_to_fetch, 
        period="6y", 
        auto_adjust=False, 
        group_by='ticker'
    )
    
    # 個別銘柄の株価データを整形
    df_prices = pd.DataFrame()
    for ticker_code in ticker_list:
        if ticker_code in hist_prices_all and not hist_prices_all[ticker_code].empty:
            temp_df = hist_prices_all[ticker_code][['Close']].copy()
            temp_df['Ticker'] = ticker_code
            df_prices = pd.concat([df_prices, temp_df])
    
    df_prices.index = pd.to_datetime(df_prices.index).tz_localize(None)
    
    # ベンチマークの株価データを整形
    benchmark_prices = hist_prices_all[benchmark_ticker][['Close']]
    benchmark_prices.index = pd.to_datetime(benchmark_prices.index).tz_localize(None)
    
    return df_prices, benchmark_prices

def fetch_financials_for_ticker(ticker_code):
    """単一銘柄の財務諸表と企業情報を取得"""
    print(f"--- Fetching financials for: {ticker_code} ---")
    ticker = yf.Ticker(ticker_code)
    
    try:
        info = ticker.info
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        
        # 必要な情報が取得できたか確認
        if financials.empty or balance_sheet.empty or not info.get('sharesOutstanding'):
            return None, None, None
            
        return financials, balance_sheet, info
    except Exception as e:
        print(f"Could not fetch data for {ticker_code}: {e}")
        return None, None, None

# 各種ファクターを計算するモジュール
import pandas as pd
import numpy as np

def normalize_series(series):
    """pandasのSeriesを正規化するヘルパー関数"""
    return (series - series.mean()) / (series.std() + 1e-8)

def calculate_base_factors(ticker_code, financials, balance_sheet):
    """単一銘柄の基本的なファクターを計算"""
    df = pd.concat([financials, balance_sheet]).T
    df.index = pd.to_datetime(df.index)

    try:
        net_income = df['Net Income']
        total_revenue = df['Total Revenue']
        total_assets = df['Total Assets']
        equity_keys = ['Total Stockholder Equity', 'Stockholders Equity']
        actual_equity_key = next((key for key in equity_keys if key in df.columns), None)
        if not actual_equity_key: return None
        stockholder_equity = df[actual_equity_key]
    except KeyError:
        return None

    analysis_df = pd.DataFrame(index=df.index)
    analysis_df['Ticker'] = ticker_code
    
    analysis_df['ProfitMargin'] = net_income / total_revenue
    analysis_df['AssetTurnover'] = total_revenue / total_assets
    analysis_df['FinancialLeverage'] = total_assets / stockholder_equity
    analysis_df['ROE'] = analysis_df['ProfitMargin'] * analysis_df['AssetTurnover'] * analysis_df['FinancialLeverage']
    
    analysis_df = analysis_df.sort_index()
    
    return analysis_df

def calculate_forward_returns(df, hist_prices):
    """将来リターンを計算"""
    periods = {'3M': 91, '6M': 182, '1Y': 365}
    for period_name, days in periods.items():
        fwd_returns = []
        for a_date in df.index:
            try:
                start_date = hist_prices.index[hist_prices.index >= a_date][0]
                end_date_target = start_date + pd.Timedelta(days=days)
                end_date = hist_prices.index[hist_prices.index >= end_date_target][0]
                start_price = hist_prices.loc[start_date, 'Close']
                end_price = hist_prices.loc[end_date, 'Close']
                fwd_returns.append((end_price - start_price) / start_price)
            except IndexError:
                fwd_returns.append(np.nan)
        df[f'Fwd_{period_name}_Return'] = fwd_returns
    return df

def calculate_forward_alphas(df, benchmark_prices):
    """超過リターン（アルファ）を計算"""
    periods = {'3M': 91, '6M': 182, '1Y': 365}
    for period_name, days in periods.items():
        alphas = []
        for idx, row in df.iterrows():
            try:
                start_date = benchmark_prices.index[benchmark_prices.index >= idx][0]
                end_date_target = start_date + pd.Timedelta(days=days)
                end_date = benchmark_prices.index[benchmark_prices.index >= end_date_target][0]
                start_price_bm = benchmark_prices.loc[start_date, 'Close']
                end_price_bm = benchmark_prices.loc[end_date, 'Close']
                bm_return = (end_price_bm - start_price_bm) / start_price_bm
                alphas.append(row[f'Fwd_{period_name}_Return'] - bm_return)
            except IndexError:
                alphas.append(np.nan)
        df[f'Fwd_{period_name}_Alpha'] = alphas
    return df

def calculate_roe_quality_score(df):
    """ROEの質を評価する「ROEクオリティスコア」を計算"""
    print("Calculating ROE Quality Score...")
    scored_groups = []
    for year, group in df.groupby(df.index.year):
        group_scored = group.copy()
        quality_score = normalize_series(group_scored['ProfitMargin']) + normalize_series(group_scored['AssetTurnover'])
        leverage_score = normalize_series(group_scored['FinancialLeverage'])
        group_scored['ROE_Quality_Score'] = quality_score - leverage_score
        scored_groups.append(group_scored)
    return pd.concat(scored_groups) if scored_groups else df.assign(ROE_Quality_Score=np.nan)

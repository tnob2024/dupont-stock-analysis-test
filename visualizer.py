# 分析結果を可視化するモジュール
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

def run_new_analyses(df):
    if df is None or df.empty: return
    
    # --- 分析①：最新データでの優良銘柄比較 ---
    print("\n[分析①] 最新データに基づく優良・注意銘柄のパフォーマンス")
    latest_df = df.groupby('Ticker').tail(1).sort_values('ROE_Quality_Score', ascending=False)
    
    top_10 = latest_df.head(10)
    bottom_10 = latest_df.tail(10)
    
    plt.figure(figsize=(12, 8))
    plt.suptitle('Latest Data: Top 10 vs Bottom 10 by ROE Quality Score', fontsize=16)
    
    ax1 = plt.subplot(2, 1, 1)
    sns.barplot(x=top_10['Ticker'], y=top_10['Fwd_1Y_Alpha'], ax=ax1, palette='summer')
    ax1.set_title('Top 10 (High Quality Score)')
    ax1.set_ylabel('1Y Forward Alpha')
    ax1.tick_params(axis='x', rotation=45)
    ax1.axhline(0, color='grey', linestyle='--')
    
    ax2 = plt.subplot(2, 1, 2)
    sns.barplot(x=bottom_10['Ticker'], y=bottom_10['Fwd_1Y_Alpha'], ax=ax2, palette='autumn')
    ax2.set_title('Bottom 10 (Low Quality Score)')
    ax2.set_ylabel('1Y Forward Alpha')
    ax2.tick_params(axis='x', rotation=45)
    ax2.axhline(0, color='grey', linestyle='--')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

    # --- 分析②：企業内での時系列比較（ヒット率分析） ---
    print("\n[分析②] 企業内時系列比較（ヒット率分析）")
    comparable_tickers = df.groupby('Ticker').filter(lambda x: len(x) >= 2)
    
    total_improvers = 0
    successful_improvers = 0
    for ticker, group in comparable_tickers.groupby('Ticker'):
        group = group.sort_index()
        # 最新の2期間を比較
        if len(group) >= 2:
            period1 = group.iloc[-2]
            period2 = group.iloc[-1]
            
            quality_improved = period2['ROE_Quality_Score'] > period1['ROE_Quality_Score']
            
            # クオリティスコアが改善した企業のみを母数とする
            if quality_improved:
                total_improvers += 1
                alpha_improved = period2['Fwd_1Y_Alpha'] > period1['Fwd_1Y_Alpha']
                # その中で、アルファも改善した場合を「ヒット」とする
                if alpha_improved:
                    successful_improvers += 1
            
    hit_rate = (successful_improvers / total_improvers) * 100 if total_improvers > 0 else 0
    
    print(f"\nROEクオリティスコアが改善した企業数: {total_improvers}社")
    print(f"そのうち、超過リターンも改善した企業数（ヒット数）: {successful_improvers}社")
    print(f"ヒット率: {hit_rate:.2f}%")
    
    plt.figure(figsize=(8, 4))
    sns.barplot(x=['Hit Rate'], y=[hit_rate], palette=['#66c2a5'])
    plt.title('Intra-Company Hit Rate Analysis')
    plt.ylabel('Hit Rate (%)')
    plt.ylim(0, 100)
    plt.text(0, hit_rate + 2, f'{hit_rate:.2f}%', ha='center', va='bottom', fontsize=14, color='black')
    plt.show()


def run_pooled_data_analysis(combined_df):
    """プールされたデータ分析を実行する。"""
    if combined_df is None or combined_df.empty: return

    print("\n--- 分析（プールデータ分析）---")
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False

    print("\n[分析1] ROE Quality Score vs. Future Returns")
    try:
        combined_df['Quality_Quintile'] = pd.qcut(combined_df['ROE_Quality_Score'], 5, labels=[f'Q{i+1}' for i in range(5)])
        quintile_returns = combined_df.groupby('Quality_Quintile')['Fwd_1Y_Alpha'].mean()
        plt.figure(figsize=(10, 6))
        quintile_returns.plot(kind='bar', color=sns.color_palette("plasma", 5))
        plt.title('Avg. 1Y Forward Alpha by ROE Quality Quintile')
        plt.xlabel('ROE Quality Quintile (Q1: Lowest -> Q5: Highest)')
        plt.ylabel('Average Alpha Return')
        plt.xticks(rotation=0)
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter('{:.1%}'.format))
        plt.show()
    except Exception as e:
        print(f"Skipping ROE Quality Quintile Analysis: {e}")

    print("\n[分析2] ROE vs. Quality Matrix Analysis")
    median_roe = combined_df['ROE'].median()
    median_quality = combined_df['ROE_Quality_Score'].median()
    combined_df['ROE_Group'] = np.where(combined_df['ROE'] > median_roe, 'High ROE', 'Low ROE')
    combined_df['Quality_Group'] = np.where(combined_df['ROE_Quality_Score'] > median_quality, 'High Quality', 'Low Quality')
    matrix_analysis = combined_df.groupby(['Quality_Group', 'ROE_Group'])['Fwd_1Y_Alpha'].mean().unstack()
    matrix_analysis = matrix_analysis.reindex(index=['High Quality', 'Low Quality'], columns=['High ROE', 'Low ROE'])
    plt.figure(figsize=(8, 6))
    sns.heatmap(matrix_analysis, annot=True, fmt='.2%', cmap='coolwarm', linewidths=.5)
    plt.title('ROE vs. Quality Matrix (Avg. 1Y Forward Alpha)')
    plt.xlabel('')
    plt.ylabel('')
    plt.show()

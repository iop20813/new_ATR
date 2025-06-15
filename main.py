import tkinter as tk
import argparse
import matplotlib.pyplot as plt
from controllers.atr_strategy_controller import ATRStrategyController
from models.atr_strategy import ATRStrategyModel

def parse_args():
    parser = argparse.ArgumentParser(description='ATR 策略回測系統')
    parser.add_argument('--cli', action='store_true', help='使用命令列模式')
    parser.add_argument('--ticker', type=str, default='0050.TW', help='股票代碼')
    parser.add_argument('--start_date', type=str, default='2010-01-01', help='開始日期')
    parser.add_argument('--atr_period', type=int, default=14, help='ATR 週期')
    parser.add_argument('--high_period', type=int, default=20, help='高點週期')
    parser.add_argument('--atr_multiplier', type=float, default=1.5, help='止損倍數')
    parser.add_argument('--profit_multiplier', type=float, default=2.0, help='獲利倍數')
    parser.add_argument('--max_hold_days', type=int, default=20, help='最大持倉天數')
    return parser.parse_args()

def plot_results(df, trades):
    """繪製結果圖表"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # 價格圖
    ax1.plot(df.index, df['Close'], label='Close Price', color='blue')
    ax1.plot(df.index, df['20D_High'], label='20D High', color='red', alpha=0.5)
    
    # 標記交易點
    for trade in trades:
        if all(key in trade for key in ['entry_date', 'entry_price', 'exit_date', 'exit_price']):
            # 進場點
            ax1.scatter(trade['entry_date'], trade['entry_price'], 
                       color='green', marker='^', s=100, label='Entry' if 'Entry' not in ax1.get_legend_handles_labels()[1] else "")
            
            # 出場點
            exit_color = 'red' if trade.get('return', 0) < 0 else 'green'
            ax1.scatter(trade['exit_date'], trade['exit_price'], 
                       color=exit_color, marker='v', s=100, label='Exit' if 'Exit' not in ax1.get_legend_handles_labels()[1] else "")
            
            # 連接進出場點
            ax1.plot([trade['entry_date'], trade['exit_date']], 
                    [trade['entry_price'], trade['exit_price']], 
                    color='gray', alpha=0.3)
            
            # 添加交易信息標籤
            trade_info = f"Return: {trade.get('return', 0):.2%}\n{trade.get('exit_reason', '')}"
            ax1.annotate(trade_info, 
                        xy=(trade['exit_date'], trade['exit_price']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=8)
    
    ax1.set_title('價格走勢與交易信號')
    ax1.legend()
    ax1.grid(True)
    
    # ATR圖
    ax2.plot(df.index, df['ATR'], label='ATR', color='purple')
    ax2.plot(df.index, df['ATR_Mean'], label='ATR Mean', color='orange', alpha=0.5)
    ax2.set_title('ATR 指標')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

def main():
    args = parse_args()
    
    if not args.cli:
        # 預設使用 GUI 介面
        root = tk.Tk()
        app = ATRStrategyController(root)
        root.mainloop()
    else:
        # 命令列模式
        strategy = ATRStrategyModel(
            ticker=args.ticker,
            start_date=args.start_date,
            atr_period=args.atr_period,
            high_period=args.high_period,
            atr_multiplier=args.atr_multiplier,
            profit_multiplier=args.profit_multiplier,
            max_hold_days=args.max_hold_days
        )
        
        # 執行回測流程
        strategy.download_data()
        strategy.calculate_atr()
        strategy.calculate_signals()
        returns, trades = strategy.backtest()
        
        # 輸出統計信息
        stats = strategy.get_statistics()
        print(f"\n=== 策略參數 ===")
        print(f"股票代碼: {args.ticker}")
        print(f"ATR 週期: {args.atr_period}")
        print(f"高點週期: {args.high_period}")
        print(f"止損倍數: {args.atr_multiplier}")
        print(f"獲利倍數: {args.profit_multiplier}")
        print(f"最大持倉天數: {args.max_hold_days}")
        
        print(f"\n=== 策略回測結果 ===")
        print(f"總報酬：{stats['total_return']:.2%}")
        print(f"交易次數：{stats['num_trades']}")
        print(f"勝率：{stats['win_rate']:.2%}")
        print(f"平均報酬：{stats['avg_return']:.2%}")
        print(f"最大回撤：{stats['max_drawdown']:.2%}")
        print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
        
        print(f"\n=== 出場原因統計 ===")
        for reason, reason_stats in stats['exit_reasons'].items():
            avg_return = sum(reason_stats['returns']) / len(reason_stats['returns']) if reason_stats['returns'] else 0
            print(f"{reason}:")
            print(f"  次數: {reason_stats['count']}")
            print(f"  平均報酬: {avg_return:.2%}")
            
        # 顯示圖表
        plot_results(strategy.df, trades)

if __name__ == "__main__":
    main() 
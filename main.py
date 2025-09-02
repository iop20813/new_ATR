import tkinter as tk
import argparse
import matplotlib.pyplot as plt
from controllers.atr_strategy_controller import ATRStrategyController
from strategies.atr_strategy import ATRStrategy
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.supertrend_strategy import SuperTrendStrategy

def parse_args():
    parser = argparse.ArgumentParser(description='交易策略回測系統')
    parser.add_argument('--cli', action='store_true', help='使用命令列模式')
    parser.add_argument('--strategy', type=str, default='atr', 
                       choices=['atr', 'ma', 'rsi', 'supertrend'], help='選擇策略 (atr, ma, rsi 或 supertrend)')
    parser.add_argument('--ticker', type=str, default='006208.TW', help='股票代碼')
    parser.add_argument('--start_date', type=str, default='2020-01-01', help='開始日期')
    # ATR 策略參數
    parser.add_argument('--atr_period', type=int, default=14, help='ATR 週期')
    parser.add_argument('--high_period', type=int, default=20, help='高點週期')
    parser.add_argument('--atr_multiplier', type=float, default=1.5, help='止損倍數')
    parser.add_argument('--profit_multiplier', type=float, default=2.0, help='獲利倍數')
    parser.add_argument('--max_hold_days', type=int, default=20, help='最大持倉天數')
    # MA 策略參數
    parser.add_argument('--short_period', type=int, default=5, help='短期均線週期')
    parser.add_argument('--long_period', type=int, default=20, help='長期均線週期')
    # RSI 策略參數
    parser.add_argument('--rsi_period', type=int, default=14, help='RSI 週期')
    parser.add_argument('--oversold', type=int, default=30, help='超賣閾值')
    parser.add_argument('--overbought', type=int, default=70, help='超買閾值')
    # SuperTrend 策略參數
    parser.add_argument('--st_period', type=int, default=10, help='SuperTrend 週期')
    parser.add_argument('--st_multiplier', type=float, default=3.0, help='SuperTrend 乘數')
    return parser.parse_args()

def plot_results(df, trades, strategy_type='atr'):
    """繪製結果圖表"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # 價格圖
    ax1.plot(df.index, df['Close'], label='Close Price', color='blue')
    
    # 根據策略類型繪製不同的指標
    if strategy_type == 'atr':
        ax1.plot(df.index, df['20D_High'], label='20D High', color='red', alpha=0.5)
        ax2.plot(df.index, df['ATR'], label='ATR', color='purple')
        ax2.plot(df.index, df['ATR_Mean'], label='ATR Mean', color='orange', alpha=0.5)
        ax2.set_title('ATR 指標')
    elif strategy_type == 'ma':
        ax1.plot(df.index, df['Fast_MA'], label='Fast MA', color='green', alpha=0.5)
        ax1.plot(df.index, df['Slow_MA'], label='Slow MA', color='red', alpha=0.5)
        ax2.plot(df.index, df['Fast_MA'] - df['Slow_MA'], label='MA Difference', color='purple')
        ax2.set_title('MA 差異')
    
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
    
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

def main():
    args = parse_args()
    
    if args.cli:
        # 命令列模式
        if args.strategy == 'atr':
            strategy = ATRStrategy(
                ticker=args.ticker,
                start_date=args.start_date,
                atr_period=args.atr_period,
                high_period=args.high_period,
                atr_multiplier=args.atr_multiplier,
                profit_multiplier=args.profit_multiplier,
                max_hold_days=args.max_hold_days
            )
        elif args.strategy == 'ma':
            strategy = MAStrategy(
                ticker=args.ticker,
                start_date=args.start_date,
                short_period=args.short_period,
                long_period=args.long_period
            )
        elif args.strategy == 'rsi':
            strategy = RSIStrategy(
                ticker=args.ticker,
                start_date=args.start_date,
                period=args.rsi_period,
                oversold=args.oversold,
                overbought=args.overbought
            )
        elif args.strategy == 'supertrend':
            strategy = SuperTrendStrategy(
                ticker=args.ticker,
                start_date=args.start_date,
                period=args.st_period,
                multiplier=args.st_multiplier
            )
        
        # 執行回測
        results = strategy.backtest()
        
        # 顯示結果
        print("\n=== 回測結果 ===")
        print(f"總報酬率: {results['total_return']:.2%}")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"最大回撤: {results['max_drawdown']:.2%}")
        print(f"勝率: {results['win_rate']:.2%}")
        print(f"交易次數: {results['num_trades']}")
        
    else:
        # GUI 模式
        root = tk.Tk()
        app = ATRStrategyController(root)
        root.mainloop()

if __name__ == '__main__':
    main() 
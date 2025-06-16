import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import warnings
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
import argparse
warnings.filterwarnings('ignore')

class ATRStrategy:
    def __init__(self, 
                 ticker="AAPL",
                 start_date="2020-01-01",
                 end_date=None,
                 atr_period=14,
                 high_period=20,
                 atr_multiplier=1.5,
                 profit_multiplier=2.0,
                 max_hold_days=20):
        """
        初始化 ATR 策略
        Args:
            ticker: 股票代碼
            start_date: 開始日期
            end_date: 結束日期，預設為今天
            atr_period: ATR 計算週期
            high_period: 高點計算週期
            atr_multiplier: 止損倍數
            profit_multiplier: 獲利倍數
            max_hold_days: 最大持倉天數
        """
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.atr_period = atr_period
        self.high_period = high_period
        self.atr_multiplier = atr_multiplier
        self.profit_multiplier = profit_multiplier
        self.max_hold_days = max_hold_days
        
        self.df = None
        self.returns = None
        self.trades = None
        
    def download_data(self):
        """下載股票數據"""
        print(f"開始下載 {self.ticker} 數據...")
        self.df = yf.download(self.ticker, period="1mo", start=self.start_date, end=self.end_date, progress=False, threads=False)
        if self.df.empty:
            raise ValueError("No data downloaded")
            
        # 修正 MultiIndex 欄位
        if isinstance(self.df.columns, pd.MultiIndex):
            self.df.columns = self.df.columns.get_level_values(0)
            
        print("數據下載完成")
        return self.df
    
    def calculate_atr(self):
        """計算 ATR 指標"""
        if self.df is None:
            raise ValueError("請先下載數據")
            
        df = self.df.copy()
        
        # 計算 True Range
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        
        # 使用 numpy 的 maximum 函數來計算 TR
        df['TR'] = np.maximum(df['H-L'], np.maximum(df['H-PC'], df['L-PC']))
        
        # 使用 EMA 而不是簡單移動平均
        df['ATR'] = df['TR'].ewm(span=self.atr_period, adjust=False).mean()
        
        self.df = df
        return df
    
    def calculate_signals(self):
        """計算交易信號"""
        if self.df is None:
            raise ValueError("請先計算 ATR")
            
        df = self.df.copy()
        
        # 計算移動平均
        df['20D_High'] = df['High'].rolling(window=self.high_period).max()
        df['ATR_Mean'] = df['ATR'].rolling(window=self.high_period).mean()
        
        # 進場信號
        df['Signal'] = 0
        
        # 確保所有需要的列都存在且對齊
        required_columns = ['Close', '20D_High', 'ATR', 'ATR_Mean']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns for signal calculation")
        
        # 使用 numpy 的 where 函數來計算信號
        close_price = df['Close'].values
        high_20d = df['20D_High'].shift(1).fillna(method='bfill').values
        atr = df['ATR'].values
        atr_mean = df['ATR_Mean'].values
        
        # 確保沒有 NaN 值
        mask = ~np.isnan(close_price) & ~np.isnan(high_20d) & ~np.isnan(atr) & ~np.isnan(atr_mean)
        signal_condition = (close_price > high_20d) & (atr > atr_mean) & mask
        
        df['Signal'] = np.where(signal_condition, 1, 0)
        
        self.df = df
        return df
    
    def backtest(self):
        """回測策略"""
        if self.df is None:
            raise ValueError("請先計算信號")
            
        df = self.df.copy()
        
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        position = 0
        entry_date = None
        returns = []
        trades = []
        
        for i in range(1, len(df)):
            current_date = df.index[i]
            
            # 進場邏輯
            if df['Signal'].iloc[i] == 1 and position == 0:
                entry_price = df['Close'].iloc[i]
                stop_loss = entry_price - self.atr_multiplier * df['ATR'].iloc[i]
                take_profit = entry_price + self.profit_multiplier * df['ATR'].iloc[i]
                position = 1
                entry_date = current_date
                trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
            
            # 出場邏輯
            elif position == 1:
                current_price = df['Close'].iloc[i]
                hold_days = (current_date - entry_date).days
                
                # 止損
                if current_price < stop_loss:
                    returns.append((current_price - entry_price) / entry_price)
                    position = 0
                    trades[-1].update({
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'return': returns[-1],
                        'exit_reason': 'stop_loss'
                    })
                
                # 獲利了結
                elif current_price > take_profit:
                    returns.append((current_price - entry_price) / entry_price)
                    position = 0
                    trades[-1].update({
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'return': returns[-1],
                        'exit_reason': 'take_profit'
                    })
                
                # 時間止損
                elif hold_days >= self.max_hold_days:
                    returns.append((current_price - entry_price) / entry_price)
                    position = 0
                    trades[-1].update({
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'return': returns[-1],
                        'exit_reason': 'time_stop'
                    })
                
                # 最後一個交易日強制平倉
                elif i == len(df) - 1:
                    returns.append((current_price - entry_price) / entry_price)
                    position = 0
                    trades[-1].update({
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'return': returns[-1],
                        'exit_reason': 'force_close'
                    })
        
        self.returns = returns
        self.trades = trades
        return returns, trades
    
    def plot_results(self):
        """繪製結果圖表"""
        if self.df is None or self.trades is None:
            raise ValueError("請先執行回測")
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 價格圖
        ax1.plot(self.df.index, self.df['Close'], label='Close Price', color='blue')
        ax1.plot(self.df.index, self.df['20D_High'], label='20D High', color='red', alpha=0.5)
        
        # 標記交易點
        for trade in self.trades:
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
        
        ax1.set_title(f'{self.ticker} Price and Trading Signals')
        ax1.legend()
        ax1.grid(True)
        
        # ATR圖
        ax2.plot(self.df.index, self.df['ATR'], label='ATR', color='purple')
        ax2.plot(self.df.index, self.df['ATR_Mean'], label='ATR Mean', color='orange', alpha=0.5)
        ax2.set_title('ATR Indicator')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def get_statistics(self):
        """獲取策略統計信息"""
        if self.returns is None or self.trades is None:
            raise ValueError("請先執行回測")
            
        returns_series = pd.Series(self.returns)
        total_return = (1 + returns_series).prod() - 1
        win_rate = len([r for r in self.returns if r > 0]) / len(self.returns)
        avg_return = np.mean(self.returns)
        max_drawdown = min(self.returns)
        sharpe_ratio = np.sqrt(252) * returns_series.mean() / returns_series.std()
        
        # 計算不同出場原因的統計
        exit_reasons = {}
        for trade in self.trades:
            reason = trade.get('exit_reason', 'unknown')
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'returns': []}
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['returns'].append(trade.get('return', 0))
        
        stats = {
            'total_return': total_return,
            'num_trades': len(self.returns),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'exit_reasons': exit_reasons
        }
        
        return stats
    
    def run(self):
        """運行完整策略"""
        try:
            # 下載數據
            self.download_data()
            
            # 計算指標
            self.calculate_atr()
            self.calculate_signals()
            
            # 回測
            self.backtest()
            
            # 獲取統計信息
            stats = self.get_statistics()
            
            # 輸出結果
            print(f"\n=== 策略參數 ===")
            print(f"股票代碼: {self.ticker}")
            print(f"ATR 週期: {self.atr_period}")
            print(f"高點週期: {self.high_period}")
            print(f"止損倍數: {self.atr_multiplier}")
            print(f"獲利倍數: {self.profit_multiplier}")
            print(f"最大持倉天數: {self.max_hold_days}")
            
            print(f"\n=== 策略回測結果 ===")
            print(f"總報酬：{stats['total_return']:.2%}")
            print(f"交易次數：{stats['num_trades']}")
            print(f"勝率：{stats['win_rate']:.2%}")
            print(f"平均報酬：{stats['avg_return']:.2%}")
            print(f"最大回撤：{stats['max_drawdown']:.2%}")
            print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
            
            print(f"\n=== 出場原因統計 ===")
            for reason, reason_stats in stats['exit_reasons'].items():
                avg_return = np.mean(reason_stats['returns'])
                print(f"{reason}:")
                print(f"  次數: {reason_stats['count']}")
                print(f"  平均報酬: {avg_return:.2%}")
            
            # 繪製圖表
            self.plot_results()
            
        except Exception as e:
            print(f"發生錯誤: {str(e)}")
            traceback.print_exc()

class ATRStrategyUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ATR 策略回測系統")
        self.window.geometry("600x500")
        
        # 創建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 股票代碼
        ttk.Label(main_frame, text="股票代碼:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ticker_var = tk.StringVar(value="006208.TW")
        ttk.Entry(main_frame, textvariable=self.ticker_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 開始日期
        ttk.Label(main_frame, text="開始日期:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar(value="2010-01-01")
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # ATR 週期
        ttk.Label(main_frame, text="ATR 週期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.atr_period_var = tk.IntVar(value=14)
        ttk.Entry(main_frame, textvariable=self.atr_period_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 高點週期
        ttk.Label(main_frame, text="高點週期:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.high_period_var = tk.IntVar(value=20)
        ttk.Entry(main_frame, textvariable=self.high_period_var, width=20).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 止損倍數
        ttk.Label(main_frame, text="止損倍數:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.atr_multiplier_var = tk.DoubleVar(value=1.5)
        ttk.Entry(main_frame, textvariable=self.atr_multiplier_var, width=20).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 獲利倍數
        ttk.Label(main_frame, text="獲利倍數:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.profit_multiplier_var = tk.DoubleVar(value=2.0)
        ttk.Entry(main_frame, textvariable=self.profit_multiplier_var, width=20).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # 最大持倉天數
        ttk.Label(main_frame, text="最大持倉天數:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.max_hold_days_var = tk.IntVar(value=20)
        ttk.Entry(main_frame, textvariable=self.max_hold_days_var, width=20).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 執行按鈕
        ttk.Button(main_frame, text="執行回測", command=self.run_backtest).grid(row=7, column=0, columnspan=2, pady=20)
        
        # 結果顯示區域
        self.result_text = tk.Text(main_frame, height=10, width=50)
        self.result_text.grid(row=8, column=0, columnspan=2, pady=10)
        
    def run_backtest(self):
        try:
            # 獲取輸入值
            strategy = ATRStrategy(
                ticker=self.ticker_var.get(),
                start_date=self.start_date_var.get(),
                atr_period=self.atr_period_var.get(),
                high_period=self.high_period_var.get(),
                atr_multiplier=self.atr_multiplier_var.get(),
                profit_multiplier=self.profit_multiplier_var.get(),
                max_hold_days=self.max_hold_days_var.get()
            )
            
            # 清空結果顯示區域
            self.result_text.delete(1.0, tk.END)
            
            # 重定向輸出到結果顯示區域
            import sys
            class TextRedirector:
                def __init__(self, text_widget):
                    self.text_widget = text_widget
                def write(self, string):
                    self.text_widget.insert(tk.END, string)
                    self.text_widget.see(tk.END)
                def flush(self):
                    pass
            
            # 保存原始stdout
            old_stdout = sys.stdout
            sys.stdout = TextRedirector(self.result_text)
            
            # 運行策略
            strategy.run()
            
            # 恢復stdout
            sys.stdout = old_stdout
            
        except Exception as e:
            messagebox.showerror("錯誤", str(e))
    
    def run(self):
        self.window.mainloop()

def parse_args():
    parser = argparse.ArgumentParser(description='ATR 策略回測系統')
    parser.add_argument('--ui', action='store_true', help='啟動UI介面')
    parser.add_argument('--ticker', type=str, default='006208.TW', help='股票代碼')
    parser.add_argument('--start_date', type=str, default='2010-01-01', help='開始日期')
    parser.add_argument('--atr_period', type=int, default=14, help='ATR 週期')
    parser.add_argument('--high_period', type=int, default=20, help='高點週期')
    parser.add_argument('--atr_multiplier', type=float, default=1.5, help='止損倍數')
    parser.add_argument('--profit_multiplier', type=float, default=2.0, help='獲利倍數')
    parser.add_argument('--max_hold_days', type=int, default=20, help='最大持倉天數')
    return parser.parse_args()

def main():
    args = parse_args()
    args.ui = True
    if args.ui:
        # 啟動UI介面
        app = ATRStrategyUI()
        app.run()
    else:
        # 命令列模式
        strategy = ATRStrategy(
            ticker=args.ticker,
            start_date=args.start_date,
            atr_period=args.atr_period,
            high_period=args.high_period,
            atr_multiplier=args.atr_multiplier,
            profit_multiplier=args.profit_multiplier,
            max_hold_days=args.max_hold_days
        )
        strategy.run()

if __name__ == "__main__":
    main()

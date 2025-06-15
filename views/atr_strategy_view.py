import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class ATRStrategyView:
    def __init__(self, root):
        self.root = root
        self.root.title("ATR 策略回測系統")
        self.root.geometry("1200x800")
        
        # 創建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 創建輸入框架
        self.input_frame = ttk.LabelFrame(self.main_frame, text="參數設置")
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 創建輸入欄位
        self.create_input_fields()
        
        # 創建按鈕框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 創建按鈕
        self.create_buttons()
        
        # 創建圖表框架
        self.chart_frame = ttk.LabelFrame(self.main_frame, text="策略表現")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 創建統計信息框架
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="統計信息")
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 初始化圖表
        self.init_chart()
        
    def create_input_fields(self):
        """創建輸入欄位"""
        # 股票代碼
        ttk.Label(self.input_frame, text="股票代碼:").grid(row=0, column=0, padx=5, pady=5)
        self.ticker_var = tk.StringVar(value="0050.TW")
        ttk.Entry(self.input_frame, textvariable=self.ticker_var).grid(row=0, column=1, padx=5, pady=5)
        
        # 開始日期
        ttk.Label(self.input_frame, text="開始日期:").grid(row=0, column=2, padx=5, pady=5)
        self.start_date_var = tk.StringVar(value="2010-01-01")
        ttk.Entry(self.input_frame, textvariable=self.start_date_var).grid(row=0, column=3, padx=5, pady=5)
        
        # 結束日期
        ttk.Label(self.input_frame, text="結束日期:").grid(row=0, column=4, padx=5, pady=5)
        self.end_date_var = tk.StringVar(value="")
        ttk.Entry(self.input_frame, textvariable=self.end_date_var).grid(row=0, column=5, padx=5, pady=5)
        
        # ATR 週期
        ttk.Label(self.input_frame, text="ATR 週期:").grid(row=1, column=0, padx=5, pady=5)
        self.atr_period_var = tk.IntVar(value=14)
        ttk.Entry(self.input_frame, textvariable=self.atr_period_var).grid(row=1, column=1, padx=5, pady=5)
        
        # 高點週期
        ttk.Label(self.input_frame, text="高點週期:").grid(row=1, column=2, padx=5, pady=5)
        self.high_period_var = tk.IntVar(value=20)
        ttk.Entry(self.input_frame, textvariable=self.high_period_var).grid(row=1, column=3, padx=5, pady=5)
        
        # ATR 乘數
        ttk.Label(self.input_frame, text="ATR 乘數:").grid(row=1, column=4, padx=5, pady=5)
        self.atr_multiplier_var = tk.DoubleVar(value=1.5)
        ttk.Entry(self.input_frame, textvariable=self.atr_multiplier_var).grid(row=1, column=5, padx=5, pady=5)
        
        # 獲利乘數
        ttk.Label(self.input_frame, text="獲利乘數:").grid(row=2, column=0, padx=5, pady=5)
        self.profit_multiplier_var = tk.DoubleVar(value=2.0)
        ttk.Entry(self.input_frame, textvariable=self.profit_multiplier_var).grid(row=2, column=1, padx=5, pady=5)
        
        # 最大持有天數
        ttk.Label(self.input_frame, text="最大持有天數:").grid(row=2, column=2, padx=5, pady=5)
        self.max_hold_days_var = tk.IntVar(value=20)
        ttk.Entry(self.input_frame, textvariable=self.max_hold_days_var).grid(row=2, column=3, padx=5, pady=5)
        
    def create_buttons(self):
        """創建按鈕"""
        # 執行回測按鈕
        self.run_button = ttk.Button(self.button_frame, text="執行回測")
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # 清除按鈕
        self.clear_button = ttk.Button(self.button_frame, text="清除")
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
    def init_chart(self):
        """初始化圖表"""
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[2, 1])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_chart(self, df, trades):
        """更新圖表"""
        self.ax1.clear()
        self.ax2.clear()
        
        # 繪製價格和信號
        self.ax1.plot(df.index, df['Close'], label='收盤價')
        self.ax1.plot(df.index, df['20D_High'], label='20日高點', alpha=0.5)
        
        # 標記交易點
        for trade in trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            
            # 繪製進場點
            self.ax1.scatter(entry_date, entry_price, color='g', marker='^')
            # 繪製出場點
            self.ax1.scatter(exit_date, exit_price, color='r', marker='v')
            
            # 連接進出場點
            self.ax1.plot([entry_date, exit_date], [entry_price, exit_price], 'k--', alpha=0.3)
        
        self.ax1.set_title('價格走勢與交易信號')
        self.ax1.legend()
        self.ax1.grid(True)
        
        # 繪製 ATR
        self.ax2.plot(df.index, df['ATR'], label='ATR')
        self.ax2.plot(df.index, df['ATR_Mean'], label='ATR 均值', alpha=0.5)
        self.ax2.set_title('ATR 指標')
        self.ax2.legend()
        self.ax2.grid(True)
        
        plt.tight_layout()
        self.canvas.draw()
        
    def update_statistics(self, stats):
        """更新統計信息"""
        # 清除現有的統計信息
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        # 創建統計信息顯示
        stats_text = f"""
        總收益率: {stats['total_return']:.2%}
        交易次數: {stats['num_trades']}
        勝率: {stats['win_rate']:.2%}
        平均收益率: {stats['avg_return']:.2%}
        最大回撤: {stats['max_drawdown']:.2%}
        夏普比率: {stats['sharpe_ratio']:.2f}
        """
        
        # 添加出場原因統計
        stats_text += "\n出場原因統計:\n"
        for reason, data in stats['exit_reasons'].items():
            avg_return = sum(data['returns']) / len(data['returns']) if data['returns'] else 0
            stats_text += f"{reason}: {data['count']}次, 平均收益率: {avg_return:.2%}\n"
            
        ttk.Label(self.stats_frame, text=stats_text, justify=tk.LEFT).pack(padx=5, pady=5)
        
    def show_error(self, message):
        """顯示錯誤信息"""
        messagebox.showerror("錯誤", message)
        
    def get_input_values(self):
        """獲取輸入值"""
        return {
            'ticker': self.ticker_var.get(),
            'start_date': self.start_date_var.get(),
            'end_date': self.end_date_var.get() or None,
            'atr_period': self.atr_period_var.get(),
            'high_period': self.high_period_var.get(),
            'atr_multiplier': self.atr_multiplier_var.get(),
            'profit_multiplier': self.profit_multiplier_var.get(),
            'max_hold_days': self.max_hold_days_var.get()
        } 
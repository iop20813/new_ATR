import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.atr_strategy import ATRStrategy
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy

class StrategyController:
    def __init__(self, main_frame):
        self.main_frame = main_frame
        self.strategies = {
            "ATR 策略": ATRStrategy,
            "移動平均線策略": MAStrategy,
            "RSI 策略": RSIStrategy
        }
        self.param_vars = {}
        self.create_ui()
    
    def create_ui(self):
        """創建使用者介面"""
        # 策略選擇
        ttk.Label(self.main_frame, text="選擇策略:").grid(row=0, column=0, sticky=tk.W)
        self.strategy_var = tk.StringVar(value="ATR 策略")
        strategy_combo = ttk.Combobox(self.main_frame, textvariable=self.strategy_var)
        strategy_combo['values'] = list(self.strategies.keys())
        strategy_combo.grid(row=0, column=1, sticky=tk.W)
        strategy_combo.bind('<<ComboboxSelected>>', self.on_strategy_change)
        
        # 股票代碼
        ttk.Label(self.main_frame, text="股票代碼:").grid(row=1, column=0, sticky=tk.W)
        self.ticker_var = tk.StringVar(value="006208.TW")
        ttk.Entry(self.main_frame, textvariable=self.ticker_var).grid(row=1, column=1, sticky=tk.W)
        
        # 開始日期
        ttk.Label(self.main_frame, text="開始日期:").grid(row=2, column=0, sticky=tk.W)
        self.start_date_var = tk.StringVar(value="2020-01-01")
        ttk.Entry(self.main_frame, textvariable=self.start_date_var).grid(row=2, column=1, sticky=tk.W)
        
        # 創建策略特定參數
        self.create_strategy_params()
    
    def create_strategy_params(self):
        """根據選擇的策略創建對應的參數輸入"""
        # 清除現有的參數輸入
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, (ttk.Label, ttk.Entry)) and widget.grid_info()['row'] > 2:
                widget.destroy()
        
        # 獲取當前選擇的策略
        strategy_name = self.strategy_var.get()
        strategy_class = self.strategies[strategy_name]
        
        # 創建策略特定參數
        row = 3
        if strategy_name == "ATR 策略":
            self.param_vars['atr_period'] = tk.IntVar(value=14)
            self.param_vars['high_period'] = tk.IntVar(value=20)
            self.param_vars['atr_multiplier'] = tk.DoubleVar(value=1.5)
            self.param_vars['profit_multiplier'] = tk.DoubleVar(value=2.0)
            self.param_vars['max_hold_days'] = tk.IntVar(value=20)
            
            ttk.Label(self.main_frame, text="ATR 週期:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['atr_period']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="高點週期:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['high_period']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="止損倍數:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['atr_multiplier']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="獲利倍數:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['profit_multiplier']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="最大持倉天數:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['max_hold_days']).grid(row=row, column=1, sticky=tk.W)
            
        elif strategy_name == "移動平均線策略":
            self.param_vars['short_period'] = tk.IntVar(value=5)
            self.param_vars['long_period'] = tk.IntVar(value=20)
            
            ttk.Label(self.main_frame, text="短期均線週期:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['short_period']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="長期均線週期:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['long_period']).grid(row=row, column=1, sticky=tk.W)
            
        elif strategy_name == "RSI 策略":
            self.param_vars['period'] = tk.IntVar(value=14)
            self.param_vars['oversold'] = tk.IntVar(value=30)
            self.param_vars['overbought'] = tk.IntVar(value=70)
            
            ttk.Label(self.main_frame, text="RSI 週期:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['period']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="超賣閾值:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['oversold']).grid(row=row, column=1, sticky=tk.W)
            row += 1
            
            ttk.Label(self.main_frame, text="超買閾值:").grid(row=row, column=0, sticky=tk.W)
            ttk.Entry(self.main_frame, textvariable=self.param_vars['overbought']).grid(row=row, column=1, sticky=tk.W)
    
    def on_strategy_change(self, event):
        """當策略改變時更新參數輸入"""
        self.create_strategy_params()
    
    def get_strategy_instance(self, data: pd.DataFrame = None):
        """根據當前選擇的策略和參數創建策略實例"""
        strategy_name = self.strategy_var.get()
        strategy_class = self.strategies[strategy_name]
        
        if strategy_name == "ATR 策略":
            return strategy_class(
                ticker=self.ticker_var.get(),
                start_date=self.start_date_var.get(),
                atr_period=self.param_vars['atr_period'].get(),
                high_period=self.param_vars['high_period'].get(),
                atr_multiplier=self.param_vars['atr_multiplier'].get(),
                profit_multiplier=self.param_vars['profit_multiplier'].get(),
                max_hold_days=self.param_vars['max_hold_days'].get()
            )
        elif strategy_name == "移動平均線策略":
            return strategy_class(
                ticker=self.ticker_var.get(),
                start_date=self.start_date_var.get(),
                short_period=self.param_vars['short_period'].get(),
                long_period=self.param_vars['long_period'].get()
            )
        elif strategy_name == "RSI 策略":
            return strategy_class(
                ticker=self.ticker_var.get(),
                start_date=self.start_date_var.get(),
                period=self.param_vars['period'].get(),
                oversold=self.param_vars['oversold'].get(),
                overbought=self.param_vars['overbought'].get()
            )

class ATRStrategyController:
    def __init__(self, root):
        self.root = root
        self.root.title("交易策略回測系統")
        
        # 創建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 創建策略控制器
        self.strategy_controller = StrategyController(self.main_frame)
        
        # 創建按鈕區域
        self.create_buttons()
        
        # 創建結果顯示區域
        self.create_result_area()
        
        # 創建圖表區域
        self.create_chart_area()
    
    def create_buttons(self):
        """創建按鈕區域"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="執行回測", command=self.run_backtest).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除結果", command=self.clear_results).pack(side=tk.LEFT, padx=5)
    
    def create_result_area(self):
        """創建結果顯示區域"""
        result_frame = ttk.LabelFrame(self.main_frame, text="回測結果", padding="5")
        result_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.result_text = tk.Text(result_frame, height=10, width=50)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def create_chart_area(self):
        """創建圖表區域"""
        chart_frame = ttk.LabelFrame(self.main_frame, text="價格走勢圖", padding="5")
        chart_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def run_backtest(self):
        """執行回測"""
        try:
            # 創建策略實例
            strategy = self.strategy_controller.get_strategy_instance()
            
            # 執行回測
            results = strategy.backtest()
            
            # 顯示結果
            self.display_results(results)
            
            # 繪製圖表
            self.plot_results(strategy.data, results['trades'])
            
        except Exception as e:
            messagebox.showerror("錯誤", str(e))
    
    def display_results(self, results):
        """顯示回測結果"""
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, "=== 回測結果 ===\n")
        self.result_text.insert(tk.END, f"總報酬率: {results['total_return']:.2%}\n")
        self.result_text.insert(tk.END, f"夏普比率: {results['sharpe_ratio']:.2f}\n")
        self.result_text.insert(tk.END, f"最大回撤: {results['max_drawdown']:.2%}\n")
        self.result_text.insert(tk.END, f"勝率: {results['win_rate']:.2%}\n")
        self.result_text.insert(tk.END, f"交易次數: {results['num_trades']}\n")
    
    def plot_results(self, data, trades):
        """繪製回測結果圖表"""
        self.ax.clear()
        
        # 繪製價格走勢
        self.ax.plot(data.index, data['Close'], label='收盤價')
        
        # 繪製交易點
        for trade in trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            
            # 繪製進場點
            self.ax.scatter(entry_date, entry_price, color='g', marker='^')
            # 繪製出場點
            self.ax.scatter(exit_date, exit_price, color='r', marker='v')
        
        self.ax.set_title('價格走勢與交易點')
        self.ax.set_xlabel('日期')
        self.ax.set_ylabel('價格')
        self.ax.legend()
        self.ax.grid(True)
        
        # 更新圖表
        self.canvas.draw()
    
    def clear_results(self):
        """清除結果"""
        self.result_text.delete(1.0, tk.END)
        self.ax.clear()
        self.canvas.draw() 
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.atr_strategy import ATRStrategy
from strategies.ma_strategy import MAStrategy
from strategies.rsi_strategy import RSIStrategy
from views.atr_strategy_view import ATRStrategyView

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
        # 建立視圖，並將控制器動作綁定
        self.view = ATRStrategyView(
            root=self.root,
            on_run_backtest=self.run_backtest,
            on_clear_results=self.clear_results,
        )

        # 策略控制器（參數區域要掛在視圖的 main_frame 上）
        self.strategy_controller = StrategyController(self.view.main_frame)

    def run_backtest(self):
        """執行回測"""
        try:
            # 創建策略實例
            strategy = self.strategy_controller.get_strategy_instance()
            
            # 執行回測
            results = strategy.backtest()
            
            # 顯示結果
            self.view.display_results(results)
            
            # 繪製圖表
            self.view.plot_results(strategy.data, results['trades'])
            
        except Exception as e:
            messagebox.showerror("錯誤", str(e))
    
    def clear_results(self):
        """清除結果"""
        self.view.clear_results()
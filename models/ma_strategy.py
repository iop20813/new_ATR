import pandas as pd
import numpy as np
from models.base_strategy import BaseStrategy

class MAStrategy(BaseStrategy):
    def __init__(self, ticker, start_date, short_period=5, long_period=20, max_hold_days=20):
        super().__init__(ticker, start_date)
        self.short_period = int(short_period)  # 確保是整數
        self.long_period = int(long_period)    # 確保是整數
        self.max_hold_days = int(max_hold_days)  # 確保是整數
        self.atr_multiplier = 2.0  # 用於計算止損
        self.profit_multiplier = 3.0  # 用於計算獲利目標
        
    def calculate_indicators(self):
        """計算移動平均線"""
        # 計算短期和長期移動平均線
        self.df['Short_MA'] = self.df['Close'].rolling(window=self.short_period).mean()
        self.df['Long_MA'] = self.df['Close'].rolling(window=self.long_period).mean()
        
        # 計算ATR用於止損
        self.df['TR'] = pd.DataFrame({
            'HL': self.df['High'] - self.df['Low'],
            'HC': abs(self.df['High'] - self.df['Close'].shift(1)),
            'LC': abs(self.df['Low'] - self.df['Close'].shift(1))
        }).max(axis=1)
        self.df['ATR'] = self.df['TR'].rolling(window=14).mean()
        
    def calculate_signals(self):
        """生成交易信號"""
        # 初始化信號列
        self.df['Signal'] = 0
        
        # 計算金叉和死叉
        golden_cross = (self.df['Short_MA'] > self.df['Long_MA']) & (self.df['Short_MA'].shift(1) <= self.df['Long_MA'].shift(1))
        death_cross = (self.df['Short_MA'] < self.df['Long_MA']) & (self.df['Short_MA'].shift(1) >= self.df['Long_MA'].shift(1))
        
        # 設置信號
        self.df.loc[golden_cross, 'Signal'] = 1  # 買入信號
        self.df.loc[death_cross, 'Signal'] = -1  # 賣出信號
        
        # 處理最大持倉天數
        position_days = 0
        for i in range(1, len(self.df)):
            if self.df['Signal'].iloc[i-1] == 1:  # 如果前一天是買入信號
                position_days += 1
                if position_days >= self.max_hold_days:
                    self.df['Signal'].iloc[i] = -1  # 強制賣出
                    position_days = 0
            elif self.df['Signal'].iloc[i-1] == -1:  # 如果前一天是賣出信號
                position_days = 0
                
    def calculate_position_size(self):
        """計算倉位大小"""
        return 100000  # 固定倉位大小 
    #test
    
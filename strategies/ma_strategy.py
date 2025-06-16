import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MAStrategy(BaseStrategy):
    def __init__(self, ticker: str, start_date: str, short_period: int = 5, long_period: int = 20):
        super().__init__(ticker, start_date)
        self.short_period = short_period
        self.long_period = long_period
    
    def get_name(self) -> str:
        return "移動平均線策略"
    
    def get_parameters(self) -> dict:
        return {
            'short_period': self.short_period,
            'long_period': self.long_period
        }
    
    def generate_signals(self) -> pd.DataFrame:
        df = self.data.copy()
        
        # 計算短期和長期移動平均線
        df['Fast_MA'] = df['Close'].rolling(window=self.short_period).mean()
        df['Slow_MA'] = df['Close'].rolling(window=self.long_period).mean()
        
        # 生成信號
        df['Signal'] = 0
        # 黃金交叉：短期均線向上穿越長期均線
        df.loc[(df['Fast_MA'] > df['Slow_MA']) & 
               (df['Fast_MA'].shift(1) <= df['Slow_MA'].shift(1)), 'Signal'] = 1
        # 死亡交叉：短期均線向下穿越長期均線
        df.loc[(df['Fast_MA'] < df['Slow_MA']) & 
               (df['Fast_MA'].shift(1) >= df['Slow_MA'].shift(1)), 'Signal'] = -1
        
        return df 
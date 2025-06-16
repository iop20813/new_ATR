import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, ticker: str, start_date: str, period: int = 14, 
                 oversold: int = 30, overbought: int = 70):
        super().__init__(ticker, start_date)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def get_name(self) -> str:
        return "RSI 策略"
    
    def get_parameters(self) -> dict:
        return {
            'period': self.period,
            'oversold': self.oversold,
            'overbought': self.overbought
        }
    
    def generate_signals(self) -> pd.DataFrame:
        df = self.data.copy()
        
        # 計算價格變化
        delta = df['Close'].diff()
        
        # 分別計算上漲和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        # 計算 RS 和 RSI
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 生成信號
        df['Signal'] = 0
        # 超賣反彈
        df.loc[(df['RSI'] < self.oversold) & 
               (df['RSI'].shift(1) < self.oversold), 'Signal'] = 1
        # 超買回落
        df.loc[(df['RSI'] > self.overbought) & 
               (df['RSI'].shift(1) > self.overbought), 'Signal'] = -1
        
        return df 
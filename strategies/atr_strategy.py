import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class ATRStrategy(BaseStrategy):
    def __init__(self, ticker: str, start_date: str, atr_period: int = 14, high_period: int = 20,
                 atr_multiplier: float = 1.5, profit_multiplier: float = 2.0,
                 max_hold_days: int = 20):
        super().__init__(ticker, start_date)
        self.atr_period = atr_period
        self.high_period = high_period
        self.atr_multiplier = atr_multiplier
        self.profit_multiplier = profit_multiplier
        self.max_hold_days = max_hold_days
    
    def get_name(self) -> str:
        return "ATR 策略"
    
    def get_parameters(self) -> dict:
        return {
            'atr_period': self.atr_period,
            'high_period': self.high_period,
            'atr_multiplier': self.atr_multiplier,
            'profit_multiplier': self.profit_multiplier,
            'max_hold_days': self.max_hold_days
        }
    
    def generate_signals(self) -> pd.DataFrame:
        df = self.data.copy()
        
        # 計算 ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(self.atr_period).mean()
        df['ATR_Mean'] = df['ATR'].rolling(window=self.atr_period).mean()
        
        # 計算高點
        df['20D_High'] = df['High'].rolling(self.high_period).max()
        
        # 生成信號
        df['Signal'] = 0
        df.loc[df['Close'] > df['20D_High'].shift(1), 'Signal'] = 1
        
        return df 
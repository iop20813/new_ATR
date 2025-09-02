import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class SuperTrendStrategy(BaseStrategy):
    def __init__(self, ticker: str, start_date: str,
                 period: int = 10, multiplier: float = 3.0):
        super().__init__(ticker, start_date)
        self.period = period
        self.multiplier = multiplier

    def get_name(self) -> str:
        return "SuperTrend 策略"

    def get_parameters(self) -> dict:
        return {
            'period': self.period,
            'multiplier': self.multiplier,
        }

    def _calculate_tr(self, df: pd.DataFrame) -> pd.Series:
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr

    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        tr = self._calculate_tr(df)
        atr = tr.rolling(window=self.period).mean()

        hl2 = (df['High'] + df['Low']) / 2.0
        upperband = hl2 + (self.multiplier * atr)
        lowerband = hl2 - (self.multiplier * atr)

        supertrend = pd.Series(index=df.index, dtype=float)
        in_uptrend = pd.Series(index=df.index, dtype=bool)

        supertrend.iloc[0] = np.nan
        in_uptrend.iloc[0] = True

        for i in range(1, len(df)):
            if df['Close'].iloc[i] > upperband.iloc[i - 1]:
                in_uptrend.iloc[i] = True
            elif df['Close'].iloc[i] < lowerband.iloc[i - 1]:
                in_uptrend.iloc[i] = False
            else:
                in_uptrend.iloc[i] = in_uptrend.iloc[i - 1]
                if in_uptrend.iloc[i] and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                    lowerband.iloc[i] = lowerband.iloc[i - 1]
                if (not in_uptrend.iloc[i]) and upperband.iloc[i] > upperband.iloc[i - 1]:
                    upperband.iloc[i] = upperband.iloc[i - 1]

            supertrend.iloc[i] = lowerband.iloc[i] if in_uptrend.iloc[i] else upperband.iloc[i]

        result = pd.DataFrame({
            'ATR': atr,
            'SuperTrend': supertrend,
            'InUptrend': in_uptrend
        }, index=df.index)
        return result

    def generate_signals(self) -> pd.DataFrame:
        df = self.data.copy()
        st = self._calculate_supertrend(df)
        df = df.join(st)

        df['Signal'] = 0
        df.loc[(df['InUptrend'] == True) & (df['InUptrend'].shift(1) == False), 'Signal'] = 1
        df.loc[(df['InUptrend'] == False) & (df['InUptrend'].shift(1) == True), 'Signal'] = -1

        return df



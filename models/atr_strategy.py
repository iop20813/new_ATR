import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

class ATRStrategyModel:
    def __init__(self, 
                 ticker="0050.TW",
                 start_date="2010-01-01",
                 end_date=None,
                 atr_period=14,
                 high_period=20,
                 atr_multiplier=1.5,
                 profit_multiplier=2.0,
                 max_hold_days=20):
        """
        初始化 ATR 策略模型
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
        self.df = yf.download(self.ticker, start=self.start_date, end=self.end_date)
        if self.df.empty:
            raise ValueError("No data downloaded")
            
        if isinstance(self.df.columns, pd.MultiIndex):
            self.df.columns = self.df.columns.get_level_values(0)
            
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
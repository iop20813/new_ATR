from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

class BaseStrategy(ABC):
    def __init__(self, ticker: str = None, start_date: str = None, data: pd.DataFrame = None):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.data = data
        self.positions = []
        self.trades = []
        
        if ticker and start_date:
            self.download_data()
    
    def download_data(self):
        """下載股票數據"""
        if not self.ticker or not self.start_date:
            raise ValueError("需要提供股票代碼和開始日期")
            
        self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date)
        if self.data.empty:
            raise ValueError(f"無法下載 {self.ticker} 的數據")
            
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data.columns = self.data.columns.get_level_values(0)
            
        return self.data
    
    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        """生成交易信號"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> dict:
        """獲取策略參數"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """獲取策略名稱"""
        pass
    
    def backtest(self) -> dict:
        """執行回測"""
        if self.data is None:
            raise ValueError("沒有數據可供回測")
            
        signals = self.generate_signals()
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        
        for i in range(len(signals)):
            current_signal = signals['Signal'].iloc[i]
            current_price = signals['Close'].iloc[i]
            current_date = signals.index[i]
            
            # 開倉
            if position == 0 and current_signal == 1:
                position = 1
                entry_price = current_price
                entry_date = current_date
            # 平倉
            elif position == 1 and current_signal == -1:
                trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': current_date,
                    'exit_price': current_price,
                    'exit_reason': '信號反轉'
                })
                position = 0
        
        # 計算報酬率
        returns, trades = self.calculate_returns(trades)
        
        # 計算績效指標
        performance = {
            'total_return': self.calculate_total_return(returns),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'max_drawdown': self.calculate_drawdown(returns),
            'win_rate': self.calculate_win_rate(trades),
            'num_trades': len(trades),
            'trades': trades
        }
        
        return performance
    
    def calculate_returns(self, trades):
        """計算交易報酬率"""
        if not trades:
            return [], []
        
        returns = []
        for trade in trades:
            if 'entry_price' in trade and 'exit_price' in trade:
                entry_price = float(trade['entry_price'])
                exit_price = float(trade['exit_price'])
                return_rate = (exit_price - entry_price) / entry_price
                returns.append(return_rate)
                trade['return'] = return_rate
        
        return returns, trades
    
    def calculate_total_return(self, returns):
        """計算總報酬率"""
        if not returns:
            return 0
        return np.prod(1 + np.array(returns)) - 1
    
    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """計算夏普比率"""
        if not returns:
            return 0
        
        returns = np.array(returns, dtype=float)
        excess_returns = returns - risk_free_rate/252
        if len(excess_returns) < 2:
            return 0
        
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    def calculate_drawdown(self, returns):
        """計算最大回撤"""
        if not returns:
            return 0
        
        returns = np.array(returns, dtype=float)
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (running_max - cumulative_returns) / running_max
        return float(np.max(drawdown))
    
    def calculate_win_rate(self, trades):
        """計算勝率"""
        if not trades:
            return 0
        
        winning_trades = sum(1 for trade in trades if trade.get('return', 0) > 0)
        return winning_trades / len(trades) 
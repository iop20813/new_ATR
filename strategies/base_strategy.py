from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import os

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

        # 準備快取檔路徑
        os.makedirs('debug_data', exist_ok=True)
        safe_ticker = str(self.ticker).replace('/', '_').replace('\\', '_')
        csv_path = f"debug_data/{safe_ticker}_{self.start_date}_{self.end_date}.csv"

        # 若 CSV 快取存在則優先載入並檢查是否涵蓋至今日（目標 end_date）
        if os.path.exists(csv_path):
            try:
                print(f"讀取快取檔案: {csv_path}")
                self.data = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                if self.data.empty:
                    raise ValueError(f"快取檔案存在但內容為空: {csv_path}")

                cached_end_date = pd.to_datetime(self.data.index.max()).normalize()
                target_end_date = pd.to_datetime(self.end_date).normalize()
                print(f"快取最後一天: {cached_end_date}, 目標最後一天: {target_end_date}（允許落後 1 天）")
                # 快取若已涵蓋至目標 end_date - 1 天，直接使用
                if cached_end_date >= (target_end_date - pd.Timedelta(days=1)):
                    print("快取已在允許範圍內（相差 1 天內），使用快取資料")
                    return self.data

                # 否則進行增量更新（從快取最後一天的下一天開始下載）
                update_start_date = (cached_end_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"快取未涵蓋至今日，增量更新: {update_start_date} -> {self.end_date}")
                incremental_data = yf.download(self.ticker, start=update_start_date, end=self.end_date)

                if isinstance(incremental_data.columns, pd.MultiIndex):
                    incremental_data.columns = incremental_data.columns.get_level_values(0)

                if not incremental_data.empty:
                    combined_data = pd.concat([self.data, incremental_data]).sort_index()
                    combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                    self.data = combined_data
                # 若沒有新增資料（例如非交易日），沿用原快取

                # 儲存更新後的快取
                try:
                    self.data.to_csv(csv_path, encoding='utf-8-sig')
                except Exception:
                    pass
                return self.data
            except Exception:
                # 快取損壞或讀取失敗，將在下方進行完整下載
                self.data = None
        else:
            # 無快取或讀取失敗，改為完整下載資料
            self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date)
        if self.data.empty:
            raise ValueError(f"無法下載 {self.ticker} 的數據")

        if isinstance(self.data.columns, pd.MultiIndex):
            self.data.columns = self.data.columns.get_level_values(0)

        # 將原始數據另存為 CSV 以利除錯
        try:
            self.data.to_csv(csv_path, encoding='utf-8-sig')
        except Exception:
            # 若寫檔失敗，忽略錯誤以免影響主流程
            pass

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
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MAHoldStrategy(BaseStrategy):
    """
    基於移動平均線的持倉不賣出策略
    在黃金交叉時買入，但不會在死亡交叉時賣出，而是持續持有
    """
    
    def __init__(self, ticker: str, start_date: str, short_period: int = 5, long_period: int = 20):
        super().__init__(ticker, start_date)
        self.short_period = short_period
        self.long_period = long_period
    
    def get_name(self) -> str:
        return "移動平均線持倉策略"
    
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
        
        # 生成信號 - 只生成買入信號，不生成賣出信號
        df['Signal'] = 0
        # 黃金交叉：短期均線向上穿越長期均線時買入
        df.loc[(df['Fast_MA'] > df['Slow_MA']) & 
               (df['Fast_MA'].shift(1) <= df['Slow_MA'].shift(1)), 'Signal'] = 1
        # 注意：不設置死亡交叉的賣出信號(-1)，實現持倉不賣出
        
        return df
    
    def backtest(self) -> dict:
        """執行回測 - 重寫以支持持倉不賣出邏輯"""
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
            
            # 只在沒有持倉時開倉
            if position == 0 and current_signal == 1:
                position = 1
                entry_price = current_price
                entry_date = current_date
                print(f"買入信號: {current_date.strftime('%Y-%m-%d')}, 價格: {current_price:.2f}")
        
        # 如果最後還有持倉，記錄為未平倉交易
        if position == 1:
            trades.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': None,  # 未平倉
                'exit_price': signals['Close'].iloc[-1],  # 當前價格
                'exit_reason': '持倉中',
                'return': (signals['Close'].iloc[-1] - entry_price) / entry_price
            })
            print(f"持倉中: 買入日期 {entry_date.strftime('%Y-%m-%d')}, 買入價格: {entry_price:.2f}, 當前價格: {signals['Close'].iloc[-1]:.2f}")
        
        # 計算報酬率用於夏普比率計算
        returns = []
        for trade in trades:
            if 'return' in trade and trade['return'] is not None:
                returns.append(trade['return'])
        
        # 計算績效指標
        performance = {
            'total_return': self.calculate_total_return_from_trades(trades),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'max_drawdown': self.calculate_drawdown(returns),
            'win_rate': self.calculate_win_rate(trades),
            'current_position': position,
            'entry_date': entry_date.strftime('%Y-%m-%d') if entry_date else None,
            'entry_price': entry_price if entry_price else 0,
            'current_price': signals['Close'].iloc[-1],
            'unrealized_return': (signals['Close'].iloc[-1] - entry_price) / entry_price if entry_price else 0,
            'num_trades': len(trades),
            'trades': trades
        }
        
        return performance
    
    def calculate_total_return_from_trades(self, trades):
        """從交易記錄計算總報酬率"""
        if not trades:
            return 0
        
        # 對於持倉不賣出策略，通常只有一筆交易
        if len(trades) == 1 and trades[0].get('return') is not None:
            return trades[0]['return']
        
        return 0
    
    def get_current_position_info(self):
        """獲取當前持倉信息"""
        if self.data is None:
            return None
            
        signals = self.generate_signals()
        position = 0
        entry_price = 0
        entry_date = None
        
        for i in range(len(signals)):
            current_signal = signals['Signal'].iloc[i]
            current_price = signals['Close'].iloc[i]
            current_date = signals.index[i]
            
            if position == 0 and current_signal == 1:
                position = 1
                entry_price = current_price
                entry_date = current_date
        
        if position == 1:
            current_price = signals['Close'].iloc[-1]
            unrealized_return = (current_price - entry_price) / entry_price
            return {
                'is_holding': True,
                'entry_date': entry_date.strftime('%Y-%m-%d'),
                'entry_price': entry_price,
                'current_price': current_price,
                'unrealized_return': unrealized_return,
                'unrealized_return_pct': unrealized_return * 100
            }
        else:
            return {
                'is_holding': False,
                'message': '目前無持倉'
            }

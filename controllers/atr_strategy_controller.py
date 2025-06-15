from models.atr_strategy import ATRStrategyModel
from views.atr_strategy_view import ATRStrategyView

class ATRStrategyController:
    def __init__(self, root):
        self.view = ATRStrategyView(root)
        self.model = None
        
        # 綁定按鈕事件
        self.view.run_button.config(command=self.run_backtest)
        self.view.clear_button.config(command=self.clear)
        
    def run_backtest(self):
        """執行回測"""
        try:
            # 獲取輸入參數
            params = self.view.get_input_values()
            
            # 創建模型實例
            self.model = ATRStrategyModel(**params)
            
            # 執行回測流程
            self.model.download_data()
            self.model.calculate_atr()
            self.model.calculate_signals()
            returns, trades = self.model.backtest()
            
            # 更新視圖
            self.view.update_chart(self.model.df, trades)
            self.view.update_statistics(self.model.get_statistics())
            
        except Exception as e:
            self.view.show_error(str(e))
            
    def clear(self):
        """清除所有輸入和顯示"""
        # 重置輸入欄位
        self.view.ticker_var.set("0050.TW")
        self.view.start_date_var.set("2010-01-01")
        self.view.end_date_var.set("")
        self.view.atr_period_var.set(14)
        self.view.high_period_var.set(20)
        self.view.atr_multiplier_var.set(1.5)
        self.view.profit_multiplier_var.set(2.0)
        self.view.max_hold_days_var.set(20)
        
        # 清除圖表
        self.view.ax1.clear()
        self.view.ax2.clear()
        self.view.canvas.draw()
        
        # 清除統計信息
        for widget in self.view.stats_frame.winfo_children():
            widget.destroy()
            
        # 重置模型
        self.model = None 
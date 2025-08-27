import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ATRStrategyView:
    def __init__(self, root, on_run_backtest, on_clear_results):
        self.root = root
        self.root.title("交易策略回測系統")

        # 主框架，提供給參數區與其他子區域使用
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 按鈕區域
        self._create_buttons(on_run_backtest, on_clear_results)

        # 結果顯示區域
        self._create_result_area()

        # 圖表區域
        self._create_chart_area()

    def _create_buttons(self, on_run_backtest, on_clear_results):
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="執行回測", command=on_run_backtest).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除結果", command=on_clear_results).pack(side=tk.LEFT, padx=5)

    def _create_result_area(self):
        result_frame = ttk.LabelFrame(self.main_frame, text="回測結果", padding="5")
        result_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.result_text = tk.Text(result_frame, height=10, width=50)
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def _create_chart_area(self):
        chart_frame = ttk.LabelFrame(self.main_frame, text="價格走勢圖", padding="5")
        chart_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def display_results(self, results):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "=== 回測結果 ===\n")
        self.result_text.insert(tk.END, f"總報酬率: {results['total_return']:.2%}\n")
        self.result_text.insert(tk.END, f"夏普比率: {results['sharpe_ratio']:.2f}\n")
        self.result_text.insert(tk.END, f"最大回撤: {results['max_drawdown']:.2%}\n")
        self.result_text.insert(tk.END, f"勝率: {results['win_rate']:.2%}\n")
        self.result_text.insert(tk.END, f"交易次數: {results['num_trades']}\n")

    def plot_results(self, data, trades):
        self.ax.clear()

        # 價格走勢
        self.ax.plot(data.index, data['Close'], label='收盤價')

        # 交易點
        for trade in trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']

            self.ax.scatter(entry_date, entry_price, color='g', marker='^')
            self.ax.scatter(exit_date, exit_price, color='r', marker='v')

        self.ax.set_title('價格走勢與交易點')
        self.ax.set_xlabel('日期')
        self.ax.set_ylabel('價格')
        self.ax.legend()
        self.ax.grid(True)

        self.canvas.draw()

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.ax.clear()
        self.canvas.draw()



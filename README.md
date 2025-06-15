# ATR 策略回測系統

這是一個基於 ATR (Average True Range) 指標的股票交易策略回測系統。系統使用 MVC 架構設計，提供了圖形化界面來進行策略參數設置和回測結果展示。

## 功能特點

- 支持自定義股票代碼和回測時間範圍
- 可調整 ATR 策略參數：
  - ATR 週期
  - 高點週期
  - ATR 乘數
  - 獲利乘數
  - 最大持有天數
- 提供策略表現圖表：
  - 價格走勢與交易信號
  - ATR 指標走勢
- 顯示詳細的統計信息：
  - 總收益率
  - 交易次數
  - 勝率
  - 平均收益率
  - 最大回撤
  - 夏普比率
  - 不同出場原因的統計

## 安裝說明

1. 確保已安裝 Python 3.8 或更高版本
2. 安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```

## 使用說明

1. 運行主程序：
   ```bash
   python main.py
   ```
2. 在界面中設置策略參數
3. 點擊"執行回測"按鈕開始回測
4. 查看回測結果和統計信息

## 系統架構

- Model (`models/atr_strategy.py`): 負責數據處理和策略邏輯
- View (`views/atr_strategy_view.py`): 負責用戶界面顯示
- Controller (`controllers/atr_strategy_controller.py`): 負責協調 Model 和 View

## 注意事項

- 股票代碼格式應符合 yfinance 的要求（例如：台股代碼需要加上 .TW 後綴）
- 日期格式應為 YYYY-MM-DD
- 建議使用較長的回測時間範圍以獲得更有意義的結果 
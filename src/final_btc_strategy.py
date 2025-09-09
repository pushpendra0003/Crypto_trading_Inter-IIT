import pandas as pd
import numpy as np
from untrade.client import Client

JUPYTER_ID = "team84_zelta_hpps"

def process_data(data):
    """
    Process the input data to add necessary indicators and transformations
    required for signal generation.
    Parameters:
    data (pandas.DataFrame): The input data.
    Returns:
    pandas.DataFrame: A dataframe with all required indicators added.
    """
    df = data.copy()    
    
    # Bollinger Bands Signal
    bb_num=10    
    df["MB"] = df["close"].rolling(bb_num).mean() 
    df["UB"] = df["MB"] + 2 * df["close"].rolling(bb_num).std(ddof=0)
    df["LB"] = df["MB"] - 2 * df["close"].rolling(bb_num).std(ddof=0)
    df["BB_signal"] = 0  
    df['BB_signal'] = np.where((df["close"] > df["MB"]) & (df["close"] <= df["UB"]) & (df['MB'] > df['MB'].rolling(6).quantile(0.80)), 1, np.where((df["close"] < df["MB"]) & (df["close"] >= df["LB"]) & (df['MB'] < df['MB'].rolling(6).quantile(0.20)), -1, 0))
    data["BB_signal"] = df["BB_signal"]
    
    # ATR Signal
    atr_num = 14
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = abs(df["high"] - df["close"].shift(1))
    df["L-PC"] = abs(df["low"] - df["close"].shift(1))
    df["TR"] = df[["H-L","H-PC","L-PC"]].max(axis=1, skipna=False)
    df["ATR"] = df["TR"].ewm(com=atr_num, min_periods=atr_num).mean()
    data["ATR"] = df["ATR"]
    
    # ADX Signal    
    adx_num = 6
    adxr_period = 4
    df["upmove"] = df["high"] - df["high"].shift(1)
    df["downmove"] = df["low"].shift(1) - df["low"]
    df["+dm"] = np.where((df["upmove"] > df["downmove"]) & (df["upmove"] > 0), df["upmove"], 0)
    df["-dm"] = np.where((df["downmove"] > df["upmove"]) & (df["downmove"] > 0), df["downmove"], 0)
    df["+di"] = 100 * (df["+dm"] / df["ATR"]).ewm(alpha=1/adx_num, min_periods=adx_num).mean()
    df["-di"] = 100 * (df["-dm"] / df["ATR"]).ewm(alpha=1/adx_num, min_periods=adx_num).mean()
    df["DX"] = 100 * abs((df["+di"] - df["-di"]) / (df["+di"] + df["-di"]))
    df["ADX"] = df["DX"].ewm(alpha=1/adx_num, min_periods=adx_num).mean()
    df["ADX_signal"] = np.where(df["ADX"] > 25, 1, 0)
    data["ADX_signal"]=df["ADX_signal"]
    df['ADXR'] = (df['ADX'] + df['ADX'].shift(adxr_period)) / 2
    df['ADXR_signal'] = np.where((df['ADXR'] >= 25) & (df['+di']>df['-di']) , 1, np.where((df['ADXR'] >= 25) & (df['+di']<df['-di']) , -1, 0))
    data['ADXR_signal'] = df['ADXR_signal']
    
    # KAMA Signal
    n = 14
    fast = 4
    slow = 30
    price_change = df['close'].diff(n).abs()
    volatility = df['close'].diff().abs().rolling(window=n).sum()
    efficiency_ratio = price_change / volatility.replace(0, np.nan)
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    sc = efficiency_ratio * fast_sc + (1 - efficiency_ratio) * slow_sc
    kama = df['close'].rolling(window=n).mean()
    for i in range(n, len(df)):
        kama.iloc[i] = kama.iloc[i - 1] + sc.iloc[i] * (df['close'].iloc[i] - kama.iloc[i - 1])
    df['KAMA'] = kama
    df['KAMA_signal'] = np.where((df['KAMA'] > df['KAMA'].rolling(10).quantile(0.95)) & (df['close'] > df['KAMA']), 1, np.where((df['KAMA'] < df['KAMA'].rolling(10).quantile(0.05)) & (df['close'] < df['KAMA']), -1,0))
    data['KAMA_signal'] = df['KAMA_signal']
    
    # TSI Signal
    long_period = 10
    short_period = 4
    price_diff = df['close'].diff()
    abs_price_diff = price_diff.abs()
    smoothed_diff = price_diff.ewm(span=long_period, adjust=False).mean()
    double_smoothed_diff = smoothed_diff.ewm(span=short_period, adjust=False).mean()
    smoothed_abs_diff = abs_price_diff.ewm(span=long_period, adjust=False).mean()
    double_smoothed_abs_diff = smoothed_abs_diff.ewm(span=short_period, adjust=False).mean()
    df['TSI'] = (double_smoothed_diff / double_smoothed_abs_diff) * 100
    df['Signal'] = df['TSI'].ewm(span=7, adjust=False).mean()
    df['TSI_signal'] = np.where((df['TSI']>df['Signal']) & ((df['Signal'] > df['Signal'].rolling(7).quantile(0.60))),1, np.where((df['TSI']<df['Signal']) & ((df['Signal'] < df['Signal'].rolling(7).quantile(0.40))),-1, 0))
    data['TSI_signal'] = df['TSI_signal']
    
    return data


def strat(data):
    """
    Generate trading signals based on processed data.
    Parameters:
    data (pandas.DataFrame): The input data containing indicators.
    Returns:
    pandas.DataFrame: The dataframe with an added 'signal' column.
    """
    data["signals"] = 0
    data["trade_type"] = "" 
    data["TP"] = 0.0              
    data["SL"] = 0.0
    tp = 0.0
    sl = 0.0                 
    position = 0
    atr_threshold = 1200
    
    for i in range(1, len(data)):
        close_price = data["close"].iloc[i]
        high_price = data["high"].iloc[i]
        low_price = data["low"].iloc[i]

        if position == 1:  
            if high_price >= tp or low_price <= sl:  
                position = 0 
        elif position == -1:  
            if low_price <= tp or high_price >= sl:  
                position = 0  
            
        # High volatility: Use EMA and ADX signals with wider SL and TP 
        if data["ATR"].iloc[i] > atr_threshold:   
            if data["KAMA_signal"].iloc[i] == data["ADXR_signal"].iloc[i] == 1 and data["TSI_signal"].iloc[i] >=0 and position <= 0:
                data.loc[i, "signals"] = 1 if position == 0 else 2
                data.loc[i,"trade_type"]="long" if position == 0 else "short_reversal"
                position = 1                
                tp = data.loc[i, 'TP'] = close_price * 1.05
                sl = data.loc[i, 'SL'] = close_price * 0.98
            elif data["KAMA_signal"].iloc[i] == data["ADXR_signal"].iloc[i] and data["TSI_signal"].iloc[i] <=0 and position >= 0:
                data.loc[i, "signals"] = -1 if position == 0 else -2
                data.loc[i,"trade_type"]="short" if position == 0 else "long_reversal"
                position = -1
                tp = data.loc[i, 'TP'] = close_price * 0.95
                sl = data.loc[i, 'SL'] = close_price * 1.02
                
        # Low volatility: Use Bollinger Bands signals with narrower SL and TP        
        else:
            if data["BB_signal"].iloc[i] == 1 and position <= 0:
                data.loc[i, "signals"] = 1 if position == 0 else 2
                data.loc[i,"trade_type"]="long" if position == 0 else "short_reversal"
                position = 1
                tp = data.loc[i, 'TP'] = close_price * 1.02
                sl = data.loc[i, 'SL'] = close_price * 0.99
            elif data["BB_signal"].iloc[i] == -1 and position >= 0:
                data.loc[i, "signals"] = -1 if position == 0 else -2
                data.loc[i,"trade_type"]="short" if position == 0 else "long_reversal"
                position = -1
                tp = data.loc[i, 'TP'] = close_price * 0.98
                sl = data.loc[i, 'SL'] = close_price * 1.01
            
    data = data.drop(columns=["BB_signal", "ADX_signal", "ATR", "ADXR_signal", "TSI_signal", "KAMA_signal"], errors="ignore")
    return data


def perform_backtest(csv_file_path):
    """
    Perform a backtest for small-sized files.
    Parameters:
    csv_file_path (str): Path to the CSV file containing backtest data.
    Returns:
    dict: Backtest results.
    """
    client = Client()
    result = client.backtest(
        jupyter_id=JUPYTER_ID,
        file_path=csv_file_path,
        leverage=1,
    )
    return result


def main():
    data = pd.read_csv("data/BTC/BTC_2019_2023_3d.csv") # Load data
    processed_data = process_data(data) # Process the data
    result_data = strat(processed_data) # Generate signals
    csv_file_path = "results.csv" # Save results to CSV
    result_data.to_csv(csv_file_path, index=False)
    backtest_result = perform_backtest(csv_file_path) # Perform backtest
    # print(backtest_result)
    for value in backtest_result:
        print(value)
    
    
if __name__ == "__main__":
    main()

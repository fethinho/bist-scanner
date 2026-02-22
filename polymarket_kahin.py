#!/usr/bin/env python3
"""
Polymarket Kahin Bot - GitHub Actions saatlik + Backtest & Accuracy.
"""
import os, requests, warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings('ignore')

TG_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")
GAMMA_BASE  = "https://gamma-api.polymarket.com"

# Emojiler
EMOJI_KAHIN   = "\U0001f52e"
EMOJI_BTC     = "\U0001f4b0"
EMOJI_ROBOT   = "\U0001f916"
EMOJI_HEDEF   = "\U0001f3af"
EMOJI_NOT     = "\U0001f4cb"
EMOJI_YESIL   = "\U0001f7e2"
EMOJI_KIRMIZI = "\U0001f534"
EMOJI_UP      = "\U0001f4c8"
EMOJI_DOWN    = "\U0001f4c9"
EMOJI_OK      = "\u2705"
EMOJI_NO      = "\U0001f6ab"
EMOJI_CHART   = "\U0001f4ca"

def get_btc_price():
    r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSD"}, timeout=10)
    r.raise_for_status()
    return float(r.json()["result"]["XXBTZUSD"]["c"][0])

def get_btc_ohlcv(interval=15, count=1000):
    r = requests.get("https://api.kraken.com/0/public/OHLC", params={"pair": "XBTUSD", "interval": interval}, timeout=15)
    r.raise_for_status()
    raw = r.json()["result"]["XXBTZUSD"]
    df = pd.DataFrame(raw, columns=["time","open","high","low","close","vwap","volume","count"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    return df[["time","open","high","low","close","volume"]].tail(count).reset_index(drop=True)

def get_poly_btc_markets():
    try:
        r = requests.get(f"{GAMMA_BASE}/markets", params={"active":"true","closed":"false","limit":50,"tag_slug":"crypto"}, timeout=15)
        r.raise_for_status()
        mkts = r.json()
        return [m for m in mkts if "BTC" in m.get("question","").upper() or "BITCOIN" in m.get("question","").upper()]
    except: return []

def build_features(df):
    d = df.copy()
    d['ret'] = d['close'].pct_change()
    d['ret_1'] = d['close'].pct_change(1)
    d['ret_3'] = d['close'].pct_change(3)
    d['sma10_ratio'] = d['close'] / d['close'].rolling(10).mean()
    d['vol10'] = d['ret'].rolling(10).std()
    
    delta = d['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    d['rsi14'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
    
    d['label'] = (d['close'].shift(-1) > d['close']).astype(int)
    return d.dropna()

FEATURES = ['ret_1','ret_3','sma10_ratio','vol10','rsi14']

def run_backtest(df_feat, test_count=100):
    X = df_feat[FEATURES].values
    y = df_feat['label'].values
    
    preds = []
    actuals = []
    returns = []
    
    # Son test_count bar icin sliding window walk-forward
    for i in range(len(df_feat) - test_count, len(df_feat)):
        X_train, y_train = X[:i], y[:i]
        X_test, y_test = X[i:i+1], y[i:i+1]
        
        m = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
        m.fit(X_train, y_train)
        
        p = m.predict(X_test)[0]
        preds.append(p)
        actuals.append(y_test[0])
        
        # Simule getiri: tahmin yonunde hareket (basit PnL)
        raw_ret = df_feat['ret'].values[i]
        sim_ret = raw_ret if p == 1 else -raw_ret
        returns.append(sim_ret)
        
    acc = np.mean(np.array(preds) == np.array(actuals))
    total_pnl = np.sum(returns)
    return acc, total_pnl

def send_telegram(token, chat_id, text):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)

def build_rapor(prob_up, btc_price, mkts, acc, pnl, test_range_text=""):
    now = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M TSİ")
    prob_down = 1 - prob_up
    sinyal = "UP" if prob_up >= 0.5 else "DOWN"
    confidence = prob_up if sinyal == "UP" else prob_down
    
    karar_emoji = EMOJI_UP if sinyal == "UP" else EMOJI_DOWN
    karar_al = (EMOJI_YESIL + " AL-UP") if sinyal == "UP" else (EMOJI_KIRMIZI + " AL-DOWN")
    
    market_q = mkts[0].get('question','BTC Marketi')[:80] if mkts else 'N/A'
    
    msg = (
        f"<b>{EMOJI_KAHIN} POLYMARKET KAHIN: BACKTEST RAPORU</b>
"
        f"<b>{now}</b>
"
        f"{'='*30}
"
        f"<b>{EMOJI_BTC} BTC Fiyat:</b> <code>${btc_price:,.2f}</code>

"
        f"<b>{EMOJI_CHART} SON 100 BAR PERFORMANS:</b>
"
        f" Accuracy: <code>{acc:.1%}</code>
"
        f" Simule PnL: <code>{pnl:+.2%}</code>

"
        f"<b>{EMOJI_ROBOT} GUNCEL TAHMIN:</b>
"
        f"{karar_emoji} <b>{sinyal}</b> (Güven: <code>{confidence:.1%}</code>)
"
        f" UP: <code>{prob_up:.1%}</code> | DOWN: <code>{prob_down:.1%}</code>

"
        f"<b>{EMOJI_HEDEF} Market:</b>
"
        f"<i>{market_q}</i>

"
        f"<b>{EMOJI_NOT} Karar: {karar_al}</b>
"
        f"{EMOJI_OK if confidence >= 0.55 else EMOJI_NO} "
        f"{'Islem Tetiklendi' if confidence >= 0.55 else 'Beklemede'}
"
        f"{'='*30}
"
        f"<i>{test_range_text}</i>
"
        f"― <i>created by FETHÍNHO</i>"
    )
    return msg

if __name__ == "__main__":
    df_raw = get_btc_ohlcv(count=1000)
    df_feat = build_features(df_raw)
    
    # 1. Backtest (Son 100 bar)
    acc, pnl = run_backtest(df_feat, test_count=100)
    
    # 2. Guncel Tahmin (En son bar)
    m_final = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
    m_final.fit(df_feat[FEATURES].values, df_feat['label'].values)
    X_last = df_feat[FEATURES].values[-1:]
    prob_up = float(m_final.predict_proba(X_last)[0][1])
    
    btc = get_btc_price()
    mkts = get_poly_btc_markets()
    
    # Zaman araligi bilgisi (UTC+3 07:00-10:00 arasi veri analizi icin not)
    # 15dk barlarinda son 12 bar yaklasik 3 saat eder.
    report = build_rapor(prob_up, btc, mkts, acc, pnl, "Test: Son 100 periyot (Walk-forward)")
    print(report)
    send_telegram(TG_TOKEN, TG_CHAT_ID, report)

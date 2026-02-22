#!/usr/bin/env python3
"""
Polymarket Kahin Bot - GitHub Actions saatlik.
"""
import os, requests, warnings
import pandas as pd
import numpy as np
from datetime import datetime
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
warnings.filterwarnings('ignore')

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GAMMA_BASE = "https://gamma-api.polymarket.com"

# Emojiler (f-string disinda tanimla)
EMOJI_KAHIN  = "\U0001f52e"
EMOJI_BTC    = "\U0001f4b0"
EMOJI_ROBOT  = "\U0001f916"
EMOJI_HEDEF  = "\U0001f3af"
EMOJI_NOT    = "\U0001f4cb"
EMOJI_YESIL  = "\U0001f7e2"
EMOJI_KIRMIZI= "\U0001f534"
EMOJI_UP     = "\U0001f4c8"
EMOJI_DOWN   = "\U0001f4c9"
EMOJI_OK     = "\u2705"
EMOJI_NO     = "\U0001f6ab"

def get_btc_price():
    r = requests.get("https://api.kraken.com/0/public/Ticker",
                     params={"pair": "XBTUSD"}, timeout=10)
    r.raise_for_status()
    return float(r.json()["result"]["XXBTZUSD"]["c"][0])

def get_btc_ohlcv(interval=15, count=720):
    r = requests.get("https://api.kraken.com/0/public/OHLC",
                     params={"pair": "XBTUSD", "interval": interval}, timeout=15)
    r.raise_for_status()
    raw = r.json()["result"]["XXBTZUSD"]
    df = pd.DataFrame(raw, columns=["time","open","high","low","close","vwap","volume","count"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    return df[["time","open","high","low","close","volume"]].tail(count).reset_index(drop=True)

def get_poly_btc_markets():
    r = requests.get(f"{GAMMA_BASE}/markets",
                     params={"active":"true","closed":"false","limit":50,"tag_slug":"crypto"}, timeout=15)
    r.raise_for_status()
    mkts = r.json()
    return [m for m in mkts if "BTC" in m.get("question","").upper() or "BITCOIN" in m.get("question","").upper()]

def build_features(df):
    d = df.copy()
    d['ret_1']  = d['close'].pct_change(1)
    d['ret_3']  = d['close'].pct_change(3)
    d['ret_6']  = d['close'].pct_change(6)
    d['ret_12'] = d['close'].pct_change(12)
    d['sma5']        = d['close'].rolling(5).mean()
    d['sma10']       = d['close'].rolling(10).mean()
    d['sma20']       = d['close'].rolling(20).mean()
    d['sma5_ratio']  = d['close'] / d['sma5']
    d['sma10_ratio'] = d['close'] / d['sma10']
    d['sma20_ratio'] = d['close'] / d['sma20']
    d['vol5']    = d['ret_1'].rolling(5).std()
    d['vol10']   = d['ret_1'].rolling(10).std()
    d['hl_ratio']= (d['high'] - d['low']) / d['close']
    d['vol_ma5'] = d['volume'].rolling(5).mean()
    d['vol_ratio']= d['volume'] / (d['vol_ma5'] + 1e-9)
    delta = d['close'].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    d['rsi14']      = 100 - (100 / (1 + gain / (loss + 1e-9)))
    ema12 = d['close'].ewm(span=12, adjust=False).mean()
    ema26 = d['close'].ewm(span=26, adjust=False).mean()
    d['macd']       = ema12 - ema26
    d['macd_signal']= d['macd'].ewm(span=9, adjust=False).mean()
    d['macd_hist']  = d['macd'] - d['macd_signal']
    d['label']      = (d['close'].shift(-1) > d['close']).astype(int)
    return d.dropna()

FEATURES = ['ret_1','ret_3','ret_6','ret_12',
            'sma5_ratio','sma10_ratio','sma20_ratio',
            'vol5','vol10','hl_ratio',
            'vol_ratio','rsi14','macd','macd_signal','macd_hist']

def train_model(df_feat):
    X, y = df_feat[FEATURES].values, df_feat['label'].values
    tscv = TimeSeriesSplit(n_splits=5)
    model = None
    for tr_idx, val_idx in tscv.split(X):
        m = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            eval_metric='logloss', verbosity=0
        )
        m.fit(X[tr_idx], y[tr_idx])
        model = m
    return model

def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        print("[TG] Token/ChatID eksik.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    if r.status_code == 200:
        print("[TG] Mesaj gonderildi!")
    else:
        print(f"[TG] Hata: {r.status_code} - {r.text[:150]}")

def build_rapor(prob_up, btc_price, mkts):
    now        = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    prob_down  = 1 - prob_up
    sinyal     = "UP" if prob_up >= 0.5 else "DOWN"
    confidence = prob_up if sinyal == "UP" else prob_down
    sep        = "=" * 32

    if sinyal == "UP" and confidence >= 0.60:
        karar_emoji = EMOJI_YESIL
        karar_text  = "GUCLU YUKSELIS"
    elif sinyal == "UP":
        karar_emoji = EMOJI_UP
        karar_text  = "YUKSELIS"
    elif sinyal == "DOWN" and confidence >= 0.60:
        karar_emoji = EMOJI_KIRMIZI
        karar_text  = "GUCLU DUSUS"
    else:
        karar_emoji = EMOJI_DOWN
        karar_text  = "DUSUS"

    market_q   = mkts[0].get('question','BTC Marketi')[:80] if mkts else 'N/A'
    market_vol = str(mkts[0].get('volume','N/A')) if mkts else 'N/A'

    if sinyal == "UP":
        karar_al = EMOJI_YESIL + " AL-UP"
    else:
        karar_al = EMOJI_KIRMIZI + " AL-DOWN"

    if confidence >= 0.55:
        islem = EMOJI_OK + " Islem Tetiklendi"
    else:
        islem = EMOJI_NO + " No-Trade Zonu (<55%)"

    msg = (
        f"<b>{EMOJI_KAHIN} POLYMARKET KAHIN RAPORU</b>\n"
        f"<b>{now}</b>\n"
        f"{sep}\n"
        f"<b>{EMOJI_BTC} BTC:</b> <code>${btc_price:,.2f}</code>\n\n"
        f"<b>{EMOJI_ROBOT} XGBoost Sinyali:</b>\n"
        f"{karar_emoji} <b>{karar_text}</b>\n"
        f"   UP  : <code>{prob_up:.1%}</code> | DOWN: <code>{prob_down:.1%}</code>\n"
        f"   Guven: <code>{confidence:.1%}</code>\n\n"
        f"<b>{EMOJI_HEDEF} Market:</b>\n"
        f"<i>{market_q}</i>\n"
        f"   Hacim: <code>{market_vol}</code>\n\n"
        f"<b>{EMOJI_NOT} Karar: {karar_al} (conf={confidence:.0%})</b>\n"
        f"{islem}\n"
        f"{sep}\n"
        f"<i>Sonraki rapor 1 saat sonra | GitHub Actions</i>"
    )
    return msg

if __name__ == "__main__":
    print(f"[{datetime.utcnow()}] Polymarket Kahin basliyor...")
    print("BTC OHLCV indiriliyor...")
    df_raw  = get_btc_ohlcv()
    df_feat = build_features(df_raw)
    btc     = get_btc_price()
    mkts    = get_poly_btc_markets()
    print(f"BTC: ${btc:,.2f} | {len(df_feat)} mum | {len(mkts)} market")
    print("Model egitiliyor...")
    model   = train_model(df_feat)
    X_son   = df_feat[FEATURES].values[-1:]
    prob_up = float(model.predict_proba(X_son)[0][1])
    sinyal  = 'UP' if prob_up >= 0.5 else 'DOWN'
    print(f"Sinyal: {sinyal} | prob_up={prob_up:.3f}")
    rapor = build_rapor(prob_up, btc, mkts)
    print("\n" + rapor)
    send_telegram(TG_TOKEN, TG_CHAT_ID, rapor)
    print("Tamamlandi.")

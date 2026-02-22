#!/usr/bin/env python3
"""
Polymarket Kahin Bot - GitHub Actions ile her saat otomatik calisir.
Kraken'dan BTC verisi alir, XGBoost ile UP/DOWN tahmini yapar,
Polymarket marketlerini ceker ve Telegram'a kahin raporu gonderir.
"""
import os, sys, requests, warnings
import pandas as pd
import numpy as np
from datetime import datetime
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
warnings.filterwarnings('ignore')

# ── Ortam degiskenleri (GitHub Secrets) ─────────────────────
TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GAMMA_BASE = "https://gamma-api.polymarket.com"

# ── 1. Veri Cekme ────────────────────────────────────────────
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

# ── 2. Feature Engineering ───────────────────────────────────
def build_features(df):
    d = df.copy()
    d['ret_1']  = d['close'].pct_change(1)
    d['ret_3']  = d['close'].pct_change(3)
    d['ret_6']  = d['close'].pct_change(6)
    d['ret_12'] = d['close'].pct_change(12)
    d['sma5']   = d['close'].rolling(5).mean()
    d['sma10']  = d['close'].rolling(10).mean()
    d['sma20']  = d['close'].rolling(20).mean()
    d['sma5_ratio']  = d['close'] / d['sma5']
    d['sma10_ratio'] = d['close'] / d['sma10']
    d['sma20_ratio'] = d['close'] / d['sma20']
    d['vol5']  = d['ret_1'].rolling(5).std()
    d['vol10'] = d['ret_1'].rolling(10).std()
    d['hl_ratio'] = (d['high'] - d['low']) / d['close']
    d['vol_ma5']   = d['volume'].rolling(5).mean()
    d['vol_ratio'] = d['volume'] / (d['vol_ma5'] + 1e-9)
    delta = d['close'].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    d['rsi14'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
    ema12 = d['close'].ewm(span=12, adjust=False).mean()
    ema26 = d['close'].ewm(span=26, adjust=False).mean()
    d['macd']        = ema12 - ema26
    d['macd_signal'] = d['macd'].ewm(span=9, adjust=False).mean()
    d['macd_hist']   = d['macd'] - d['macd_signal']
    d['label'] = (d['close'].shift(-1) > d['close']).astype(int)
    return d.dropna()

FEATURES = ['ret_1','ret_3','ret_6','ret_12',
            'sma5_ratio','sma10_ratio','sma20_ratio',
            'vol5','vol10','hl_ratio',
            'vol_ratio','rsi14','macd','macd_signal','macd_hist']

# ── 3. Model Egitimi ─────────────────────────────────────────
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

# ── 4. Telegram Gonderici ────────────────────────────────────
def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        print("[TG] Token/ChatID eksik, atlanıyor.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    if r.status_code == 200:
        print("[TG] Mesaj gonderildi!")
    else:
        print(f"[TG] Hata: {r.status_code} - {r.text[:150]}")

# ── 5. Rapor Olusturucu ──────────────────────────────────────
def build_rapor(prob_up, btc_price, mkts):
    now  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    prob_down  = 1 - prob_up
    sinyal     = "UP" if prob_up >= 0.5 else "DOWN"
    confidence = prob_up if sinyal == "UP" else prob_down
    karar_emoji = "\U0001f7e2" if sinyal == "UP" and confidence >= 0.60 else \
                  "\U0001f4c8" if sinyal == "UP" else \
                  "\U0001f534" if confidence >= 0.60 else "\U0001f4c9"
    karar_text  = ("GUCLU " if confidence >= 0.60 else "") + ("YUKSELIS" if sinyal == "UP" else "DUSUS")
    market_q   = mkts[0].get('question','BTC Marketi')[:80] if mkts else 'N/A'
    market_vol = mkts[0].get('volume','N/A') if mkts else 'N/A'
    islem      = "\u2705 Islem Tetiklendi" if confidence >= 0.55 else "\U0001f6ab No-Trade Zonu (<55%)"

    return f"""
<b>\U0001f52e POLYMARKET KAHIN RAPORU</b>
<b>{now}</b>
{'=' * 32}
<b>\U0001f4b0 BTC:</b> <code>${btc_price:,.2f}</code>

<b>\U0001f916 XGBoost Sinyali:</b>
{karar_emoji} <b>{karar_text}</b>
   UP  : <code>{prob_up:.1%}</code> | DOWN: <code>{prob_down:.1%}</code>
   Guven: <code>{confidence:.1%}</code>

<b>\U0001f3af Market:</b>
<i>{market_q}</i>
   Hacim: <code>{market_vol}</code>

<b>\U0001f4cb Karar: {'\U0001f7e2 AL-UP' if sinyal=='UP' else '\U0001f534 AL-DOWN'} (conf={confidence:.0%})</b>
{islem}
{'=' * 32}
<i>Sonraki rapor 1 saat sonra | GitHub Actions</i>
""".strip()

# ── ANA AKIS ─────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.utcnow()}] Polymarket Kahin basliyor...")

    # Veri
    print("BTC OHLCV indiriliyor...")
    df_raw  = get_btc_ohlcv()
    df_feat = build_features(df_raw)
    btc     = get_btc_price()
    mkts    = get_poly_btc_markets()
    print(f"BTC: ${btc:,.2f} | {len(df_feat)} mum | {len(mkts)} market")

    # Model
    print("Model egitiliyor...")
    model = train_model(df_feat)
    X_son = df_feat[FEATURES].values[-1:]
    prob_up = float(model.predict_proba(X_son)[0][1])
    print(f"Sinyal: {'UP' if prob_up>=0.5 else 'DOWN'} | prob_up={prob_up:.3f}")

    # Rapor
    rapor = build_rapor(prob_up, btc, mkts)
    print("\n" + rapor)

    # TG
    send_telegram(TG_TOKEN, TG_CHAT_ID, rapor)
    print("Tamamlandi.")

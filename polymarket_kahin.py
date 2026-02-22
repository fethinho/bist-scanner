#!/usr/bin/env python3
import os, requests, warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import xgboost as xgb

warnings.filterwarnings('ignore')

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GAMMA_BASE = "https://gamma-api.polymarket.com"
UTC3 = timezone(timedelta(hours=3))
CONF_THRESHOLD = 0.65

EMOJI_KAHIN = "\\U0001f52e"
EMOJI_BTC = "\\U0001f4b0"
EMOJI_ROBOT = "\\U0001f916"
EMOJI_HEDEF = "\\U0001f3af"
EMOJI_NOT = "\\U0001f4cb"
EMOJI_YESIL = "\\U0001f7e2"
EMOJI_KIRMIZI = "\\U0001f534"
EMOJI_UP = "\\U0001f4c8"
EMOJI_DOWN = "\\U0001f4c9"
EMOJI_OK = "\\u2705"
EMOJI_NO = "\\U0001f6ab"
EMOJI_CHART = "\\U0001f4ca"
EMOJI_CLOCK = "\\U0001f553"
NL = "
"
"

def now_utc3():
    return datetime.now(UTC3)

def get_btc_price():
    r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSD"}, timeout=10)
    r.raise_for_status()
    return float(r.json()["result"]["XXBTZUSD"]["c"][0])

def get_btc_ohlcv(interval=60, count=1000):
    r = requests.get("https://api.kraken.com/0/public/OHLC", params={"pair": "XBTUSD", "interval": interval}, timeout=15)
    r.raise_for_status()
    raw = r.json()["result"]["XXBTZUSD"]
    df = pd.DataFrame(raw, columns=["time","open","high","low","close","vwap","volume","count"])
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("Europe/Istanbul")
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    return df[["time","open","high","low","close","volume"]].tail(count).reset_index(drop=True)

def get_poly_btc_markets():
    try:
        r = requests.get(f"{GAMMA_BASE}/markets", params={"active":"true","closed":"false","limit":50,"tag_slug":"crypto"}, timeout=15)
        r.raise_for_status()
        return [m for m in r.json() if "BTC" in m.get("question","").upper()]
    except:
        return []

def build_features(df):
    d = df.copy()
    d['ret'] = d['close'].pct_change()
    d['ret_1'] = d['close'].pct_change(1)
    d['ret_3'] = d['close'].pct_change(3)
    d['ret_6'] = d['close'].pct_change(6)
    d['sma10_ratio']= d['close'] / d['close'].rolling(10).mean()
    d['sma20_ratio']= d['close'] / d['close'].rolling(20).mean()
    d['vol10'] = d['ret'].rolling(10).std()
    d['hl_ratio'] = (d['high'] - d['low']) / d['close']
    delta = d['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    d['rsi14'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
    ema12 = d['close'].ewm(span=12, adjust=False).mean()
    ema26 = d['close'].ewm(span=26, adjust=False).mean()
    d['macd'] = ema12 - ema26
    d['macd_sig'] = d['macd'].ewm(span=9, adjust=False).mean()
    d['label'] = (d['close'].shift(-1) > d['close']).astype(int)
    return d.dropna()

FEATURES = ['ret_1','ret_3','ret_6','sma10_ratio','sma20_ratio','vol10','hl_ratio','rsi14','macd','macd_sig']

def run_backtest(df_feat, test_count=48, conf_min=0.65):
    X = df_feat[FEATURES].values
    y = df_feat['label'].values
    all_preds, all_actuals, all_returns = [], [], []
    filtered_preds, filtered_actuals, filtered_returns = [], [], []
    start = len(df_feat) - test_count
    for i in range(start, len(df_feat)):
        m = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
        m.fit(X[:i], y[:i])
        prob = m.predict_proba(X[i:i+1])[0]
        p = int(np.argmax(prob))
        conf = float(max(prob))
        ret = float(df_feat['ret'].values[i])
        sim_ret = ret if p == 1 else -ret
        all_preds.append(p); all_actuals.append(int(y[i])); all_returns.append(sim_ret)
        if conf >= conf_min:
            filtered_preds.append(p); filtered_actuals.append(int(y[i])); filtered_returns.append(sim_ret)
    acc_all = float(np.mean(np.array(all_preds) == np.array(all_actuals)))
    pnl_all = float(np.sum(all_returns))
    n_filt = len(filtered_preds)
    acc_filt = float(np.mean(np.array(filtered_preds) == np.array(filtered_actuals))) if n_filt > 0 else 0.0
    pnl_filt = float(np.sum(filtered_returns)) if n_filt > 0 else 0.0
    return acc_all, pnl_all, acc_filt, pnl_filt, n_filt

def send_telegram(token, chat_id, text):
    if not token or not chat_id: return
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)

def build_rapor(prob_up, btc, mkts, acc_all, pnl_all, acc_filt, pnl_filt, n_filt):
    ts = now_utc3().strftime("%Y-%m-%d %H:%M UTC+3")
    sinyal = "UP" if prob_up >= 0.5 else "DOWN"
    conf = prob_up if sinyal == "UP" else (1-prob_up)
    karar_emoji = EMOJI_UP if sinyal == "UP" else EMOJI_DOWN
    karar_al = (EMOJI_YESIL + " AL-UP") if sinyal == "UP" else (EMOJI_KIRMIZI + " AL-DOWN")
    islem_dur = (EMOJI_OK + " ISLEM TETIKLENDI (conf>65%)") if conf >= CONF_THRESHOLD else (EMOJI_NO + " NO-TRADE ZONU (conf&lt;65%)")
    sep = "=" * 28
    fmt = lambda v: "{:.1f}%".format(v * 100)
    msg = [
        f"**{EMOJI_KAHIN} POLYMARKET KAHIN RAPORU**",
        f"**{EMOJI_CLOCK} {ts}**", sep,
        f"**{EMOJI_BTC} BTC:** `${btc:,.2f}`", "",
        f"**{EMOJI_CHART} BACKTEST SON 48 SAAT (1s):**", "",
        f" **Tum Sinyaller:**\
 Accuracy: `{fmt(acc_all)}` | PnL: `{pnl_all*100:+.2f}%`\
",
        f" **conf > 65% ({n_filt} islem):**\
 Accuracy: `{fmt(acc_filt)}` | PnL: `{pnl_filt*100:+.2f}%`\
",
        sep, f"**{EMOJI_ROBOT} TAHMIN (1s):**\
{karar_emoji} **{sinyal}** Guven: `{fmt(conf)}`\
",
        f"**{EMOJI_HEDEF} Market:**\
_{mkts[0].get('question','BTC')[:60] if mkts else 'N/A'}_\
",
        f"**{EMOJI_NOT} Karar: {karar_al}**\
{islem_dur}\
", sep,
        "_Walk-forward | 1s bar | UTC+3_", "\\u2015 _created by FETHINHO_"
    ]
    return "\
".join(msg)

if __name__ == "__main__":
    df = build_features(get_btc_ohlcv(interval=60))
    acc_all, pnl_all, acc_filt, pnl_filt, n_filt = run_backtest(df)
    m = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
    m.fit(df[FEATURES].values, df['label'].values)
    prob_up = float(m.predict_proba(df[FEATURES].values[-1:])[0][1])
    rapor = build_rapor(prob_up, get_btc_price(), get_poly_btc_markets(), acc_all, pnl_all, acc_filt, pnl_filt, n_filt)
    print(rapor); send_telegram(TG_TOKEN, TG_CHAT_ID, rapor)

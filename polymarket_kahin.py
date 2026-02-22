#!/usr/bin/env python3
"""
Polymarket Kahin Bot - conf>60% filtreli backtest + UTC+3 zaman dilimi
"""
import os, requests, warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import xgboost as xgb
warnings.filterwarnings('ignore')

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GAMMA_BASE = "https://gamma-api.polymarket.com"
UTC3       = timezone(timedelta(hours=3))
CONF_THRESHOLD = 0.60

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
EMOJI_CLOCK   = "\U0001f553"
NL = "\n"

def now_utc3():
    return datetime.now(UTC3)

def get_btc_price():
    r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSD"}, timeout=10)
    r.raise_for_status()
    return float(r.json()["result"]["XXBTZUSD"]["c"][0])

def get_btc_ohlcv(interval=15, count=1000):
    r = requests.get("https://api.kraken.com/0/public/OHLC",
                     params={"pair": "XBTUSD", "interval": interval}, timeout=15)
    r.raise_for_status()
    raw = r.json()["result"]["XXBTZUSD"]
    df = pd.DataFrame(raw, columns=["time","open","high","low","close","vwap","volume","count"])
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("Europe/Istanbul")
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    return df[["time","open","high","low","close","volume"]].tail(count).reset_index(drop=True)

def get_poly_btc_markets():
    try:
        r = requests.get(f"{GAMMA_BASE}/markets",
                         params={"active":"true","closed":"false","limit":50,"tag_slug":"crypto"}, timeout=15)
        r.raise_for_status()
        mkts = r.json()
        return [m for m in mkts if "BTC" in m.get("question","").upper() or "BITCOIN" in m.get("question","").upper()]
    except:
        return []

def build_features(df):
    d = df.copy()
    d['ret']        = d['close'].pct_change()
    d['ret_1']      = d['close'].pct_change(1)
    d['ret_3']      = d['close'].pct_change(3)
    d['ret_6']      = d['close'].pct_change(6)
    d['sma10_ratio']= d['close'] / d['close'].rolling(10).mean()
    d['sma20_ratio']= d['close'] / d['close'].rolling(20).mean()
    d['vol10']      = d['ret'].rolling(10).std()
    d['hl_ratio']   = (d['high'] - d['low']) / d['close']
    delta = d['close'].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    d['rsi14']      = 100 - (100 / (1 + gain / (loss + 1e-9)))
    ema12 = d['close'].ewm(span=12, adjust=False).mean()
    ema26 = d['close'].ewm(span=26, adjust=False).mean()
    d['macd']       = ema12 - ema26
    d['macd_sig']   = d['macd'].ewm(span=9, adjust=False).mean()
    d['label']      = (d['close'].shift(-1) > d['close']).astype(int)
    return d.dropna()

FEATURES = ['ret_1','ret_3','ret_6','sma10_ratio','sma20_ratio','vol10','hl_ratio','rsi14','macd','macd_sig']

def run_backtest(df_feat, test_count=100, conf_min=0.60):
    X = df_feat[FEATURES].values
    y = df_feat['label'].values
    times = df_feat['time'].values if 'time' in df_feat.columns else [None]*len(df_feat)

    all_preds, all_actuals, all_returns = [], [], []
    filtered_preds, filtered_actuals, filtered_returns = [], [], []
    trade_times = []

    start = len(df_feat) - test_count
    for i in range(start, len(df_feat)):
        m = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
        m.fit(X[:i], y[:i])
        prob = m.predict_proba(X[i:i+1])[0]
        p    = int(np.argmax(prob))
        conf = float(max(prob))
        raw_ret = float(df_feat['ret'].values[i])
        sim_ret = raw_ret if p == 1 else -raw_ret

        all_preds.append(p)
        all_actuals.append(int(y[i]))
        all_returns.append(sim_ret)

        if conf >= conf_min:
            filtered_preds.append(p)
            filtered_actuals.append(int(y[i]))
            filtered_returns.append(sim_ret)
            trade_times.append(str(times[i])[:16] if times[i] is not None else "")

    acc_all      = float(np.mean(np.array(all_preds) == np.array(all_actuals)))
    pnl_all      = float(np.sum(all_returns))
    n_filtered   = len(filtered_preds)
    acc_filtered = float(np.mean(np.array(filtered_preds) == np.array(filtered_actuals))) if n_filtered > 0 else 0.0
    pnl_filtered = float(np.sum(filtered_returns)) if n_filtered > 0 else 0.0

    return acc_all, pnl_all, acc_filtered, pnl_filtered, n_filtered, trade_times

def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        print("[TG] Token/ChatID eksik.")
        return
    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    if r.status_code == 200:
        print("[TG] Mesaj gonderildi!")
    else:
        print("[TG] Hata: " + str(r.status_code) + " - " + r.text[:150])

def build_rapor(prob_up, btc_price, mkts,
                acc_all, pnl_all,
                acc_filt, pnl_filt, n_filt,
                test_count=100):
    ts = now_utc3().strftime("%Y-%m-%d %H:%M UTC+3")
    prob_down  = 1.0 - prob_up
    sinyal     = "UP" if prob_up >= 0.5 else "DOWN"
    confidence = prob_up if sinyal == "UP" else prob_down
    karar_emoji= EMOJI_UP if sinyal == "UP" else EMOJI_DOWN
    karar_al   = (EMOJI_YESIL + " AL-UP") if sinyal == "UP" else (EMOJI_KIRMIZI + " AL-DOWN")
    market_q   = mkts[0].get('question','BTC Marketi')[:80] if mkts else 'N/A'

    if confidence >= CONF_THRESHOLD:
        islem_dur = EMOJI_OK + " ISLEM TETIKLENDI (conf>60%)"
    else:
        islem_dur = EMOJI_NO + " NO-TRADE ZONU (conf<60%)"

    sep = "=" * 28
    fmt = lambda v: "{:.1f}".format(v * 100) + "%"

    lines = [
        "<b>" + EMOJI_KAHIN + " POLYMARKET KAHIN RAPORU</b>",
        "<b>" + EMOJI_CLOCK + " " + ts + "</b>",
        sep,
        "<b>" + EMOJI_BTC + " BTC:</b> <code>$" + "{:,.2f}".format(btc_price) + "</code>",
        "",
        "<b>" + EMOJI_CHART + " BACKTEST SON " + str(test_count) + " BAR (15dk):</b>",
        "",
        "  <b>Tum Sinyaller:</b>",
        "    Accuracy : <code>" + fmt(acc_all) + "</code>",
        "    Simule PnL: <code>" + ("{:+.2f}".format(pnl_all * 100)) + "%</code>",
        "",
        "  <b>Yalnizca conf &gt; 60% Sinyaller (" + str(n_filt) + " islem):</b>",
        "    Accuracy : <code>" + fmt(acc_filt) + "</code>",
        "    Simule PnL: <code>" + ("{:+.2f}".format(pnl_filt * 100)) + "%</code>",
        "",
        sep,
        "<b>" + EMOJI_ROBOT + " GUNCEL TAHMIN:</b>",
        karar_emoji + " <b>" + sinyal + "</b>  Guven: <code>" + fmt(confidence) + "</code>",
        "  UP: <code>" + fmt(prob_up) + "</code>  DOWN: <code>" + fmt(prob_down) + "</code>",
        "",
        "<b>" + EMOJI_HEDEF + " Market:</b>",
        "<i>" + market_q + "</i>",
        "",
        "<b>" + EMOJI_NOT + " Karar: " + karar_al + "</b>",
        islem_dur,
        sep,
        "<i>Walk-forward | 15dk bar | UTC+3 zaman dilimi</i>",
        "\u2015 <i>created by FETHINHO</i>"
    ]
    return NL.join(lines)

if __name__ == "__main__":
    t_start = now_utc3()
    print("[" + t_start.strftime("%Y-%m-%d %H:%M UTC+3") + "] Polymarket Kahin basliyor...")

    df_raw  = get_btc_ohlcv(count=1000)
    df_feat = build_features(df_raw)
    print("Veri: " + str(len(df_feat)) + " bar | En erken: " + str(df_feat['time'].iloc[0])[:16] + " | En son: " + str(df_feat['time'].iloc[-1])[:16])

    print("Walk-forward backtest (son 100 bar, conf>" + str(int(CONF_THRESHOLD*100)) + "%) calistirilıyor...")
    acc_all, pnl_all, acc_filt, pnl_filt, n_filt, trade_times = run_backtest(df_feat, test_count=100, conf_min=CONF_THRESHOLD)

    print("--- TUM ---  Acc: " + str(round(acc_all*100,1)) + "%  PnL: " + str(round(pnl_all*100,2)) + "%")
    print("--- FILT ---  Acc: " + str(round(acc_filt*100,1)) + "%  PnL: " + str(round(pnl_filt*100,2)) + "%  N: " + str(n_filt))

    m_final = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
    m_final.fit(df_feat[FEATURES].values, df_feat['label'].values)
    X_last  = df_feat[FEATURES].values[-1:]
    prob_up = float(m_final.predict_proba(X_last)[0][1])
    sinyal  = "UP" if prob_up >= 0.5 else "DOWN"
    conf    = prob_up if prob_up >= 0.5 else 1 - prob_up
    print("Guncel Sinyal: " + sinyal + " | prob_up=" + str(round(prob_up,3)) + " | conf=" + str(round(conf,3)))

    btc  = get_btc_price()
    mkts = get_poly_btc_markets()

    report = build_rapor(prob_up, btc, mkts,
                         acc_all, pnl_all,
                         acc_filt, pnl_filt, n_filt,
                         test_count=100)
    print(report)
    send_telegram(TG_TOKEN, TG_CHAT_ID, report)
    t_end = now_utc3()
    print("Tamamlandi. Sure: " + str((t_end - t_start).seconds) + "s")

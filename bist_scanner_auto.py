import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import pytz

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8460458441:AAG81QuP0nDc0AT5SYON63bus2d0udab0Iw"
TELEGRAM_CHAT_ID = "314746106"

# BIST Tickers
BIST_TICKERS = [
    "THYAO.IS", "ASELS.IS", "EREGL.IS", "SISE.IS", "KCHOL.IS",
    "SAHOL.IS", "AKBNK.IS", "TUPRS.IS", "VAKBN.IS", "ISCTR.IS",
    "GARAN.IS", "TTKOM.IS", "TAVHL.IS", "ENKAI.IS", "PETKM.IS",
    "KOZAL.IS", "KOZAA.IS", "BIMAS.IS", "ARCLK.IS", "EKGYO.IS",
    "HEKTS.IS", "KRDMD.IS", "FROTO.IS", "TOASO.IS", "TCELL.IS",
    "VESTL.IS", "PGSUS.IS", "AEFES.IS", "DOHOL.IS", "ODAS.IS"
]

def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram mesajı gönderildi")
        else:
            print(f"❌ Telegram hatası: {response.text}")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def scan_stock_15m(ticker):
    """Scan a single stock for 15m timeframe"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="5d", interval="15m")
        
        if len(data) < 20:
            return None
        
        # Calculate indicators
        data['RSI'] = calculate_rsi(data)
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        rsi = last_row['RSI']
        close = last_row['Close']
        sma20 = last_row['SMA20']
        
        # Signal conditions
        signal = None
        if rsi < 30 and close > sma20:
            signal = "🟢 AL Sinyali"
        elif rsi > 70 and close < sma20:
            signal = "🔴 SAT Sinyali"
        
        if signal:
            return {
                'ticker': ticker.replace('.IS', ''),
                'signal': signal,
                'rsi': round(rsi, 2),
                'price': round(close, 2)
            }
    except Exception as e:
        print(f"Hata {ticker}: {str(e)}")
    
    return None

def run_15m_scan():
    """Run 15m scan for all BIST stocks"""
    print("\n🔍 15 Dakika Tarama Başladı...")
    
    results = []
    for ticker in BIST_TICKERS:
        result = scan_stock_15m(ticker)
        if result:
            results.append(result)
    
    # Prepare Telegram message
    turkey_tz = pytz.timezone('Europe/Istanbul')
    now = datetime.now(turkey_tz)
    
    message = f"<b>📊 BIST 15 Dakika Tarama Sonuçları</b>\n"
    message += f"<b>🕐 Tarih:</b> {now.strftime('%d.%m.%Y %H:%M')} (UTC+3)\n\n"
    
    if results:
        for r in results:
            message += f"<b>{r['ticker']}</b> {r['signal']}\n"
            message += f"  RSI: {r['rsi']} | Fiyat: {r['price']} TL\n\n"
    else:
        message += "❌ Sinyal bulunamadı\n"
    
    # Send to Telegram
    send_telegram_message(message)
    print(f"\n✅ Tarama tamamlandı. {len(results)} sinyal bulundu.")

if __name__ == "__main__":
    run_15m_scan()

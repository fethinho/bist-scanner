#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merdiven Hacim Taraması - BIST Hisse Senedi Analizi
Hacim artışı ve yeşil bar koşullarını kontrol eder
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval
from tradingview_screener import get_all_symbols
import requests

# Telegram ayarları
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Telegram'a mesaj gönder"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram ayarları bulunamadı!")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Telegram mesajı gönderildi")
            return True
        else:
            print(f"❌ Telegram hatası: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram bağlantı hatası: {e}")
        return False

def main():
    print("🚀 Merdiven Hacim Taraması Başlatılıyor...")
    
    # TvDatafeed bağlantısı
    try:
        tv = TvDatafeed()
        print("✅ TvDatafeed bağlantısı kuruldu")
    except Exception as e:
        print(f"❌ TvDatafeed bağlantı hatası: {e}")
        return
    
    # BIST hisselerini al
    print("📊 BIST hisseleri yükleniyor...")
    hisseler = sorted([s.replace('BIST:', '') for s in get_all_symbols(market='turkey')])
    print(f"✅ {len(hisseler)} hisse bulundu")
    
    # Tarama parametreleri
    interval = Interval.in_daily
    interval_label = "Günlük"
    sma_period = 10
    n_bars_to_fetch = 50
    min_bars_required = 10
    yesil_tanim = 'co'  # close > open
    yesil_mod = 'strict'  # son 3 bar yeşil
    
    sonuclar_full = []
    sonuclar_ladder = []
    
    print(f"🔍 Tarama başlıyor: {interval_label} periyot")
    
    # Hisseleri tara
    for idx, hisse in enumerate(hisseler, 1):
        if idx % 50 == 0:
            print(f"⏳ İlerleme: {idx}/{len(hisseler)}")
        
        try:
            # Veri çek
            data = tv.get_hist(hisse, exchange='BIST', interval=interval, n_bars=n_bars_to_fetch)
            
            # Veri kontrolü
            if data is None or data.empty or len(data) < min_bars_required:
                continue
            
            # Hacim SMA hesapla
            data['volume_sma10'] = data['volume'].rolling(window=sma_period).mean()
            
            # NaN temizle
            data = data.dropna(subset=['volume', 'volume_sma10'])
            
            if len(data) < 4:
                continue
            
            # Yeşil bar tanımları
            data['green_co'] = data['close'] > data['open']
            data['green_pc'] = data['close'] > data['close'].shift(1)
            green_col = 'green_co' if yesil_tanim == 'co' else 'green_pc'
            
            # Son çubuk değerleri
            last_volume = data['volume'].iloc[-1]
            prev_volume = data['volume'].iloc[-2]
            prev2_volume = data['volume'].iloc[-3]
            prev3_volume = data['volume'].iloc[-4]
            last_volume_sma = data['volume_sma10'].iloc[-1]
            
            # Hacim merdiven koşulu
            condition_increasing_volume = (last_volume > prev_volume) and \
                                        (prev_volume > prev2_volume) and \
                                        (prev2_volume > prev3_volume)
            
            # SMA üstü kontrol
            condition_above_sma = last_volume > last_volume_sma
            
            # Yeşil bar şartları
            condition_green_bars_strict = bool(data[green_col].iloc[-1] and
                                             data[green_col].iloc[-2] and
                                             data[green_col].iloc[-3])
            condition_green_bars_flexible = bool(data[green_col].iloc[-1])
            condition_green = condition_green_bars_strict if yesil_mod == 'strict' else condition_green_bars_flexible
            
            # Merdiven + Yeşil koşulu
            if condition_increasing_volume and condition_green:
                base_rec = {
                    'Hisse': hisse,
                    'Son Hacim': int(last_volume),
                    'Önceki Hacim': int(prev_volume),
                    '2 Önceki Hacim': int(prev2_volume),
                    '3 Önceki Hacim': int(prev3_volume),
                    f'Hacim SMA({sma_period})': round(last_volume_sma, 2),
                    'Son Bar Yeşil': 'Evet' if data[green_col].iloc[-1] else 'Hayır'
                }
                sonuclar_ladder.append(base_rec)
                
                # SMA üstü de sağlanıyorsa full listesine ekle
                if condition_above_sma:
                    sonuclar_full.append(base_rec.copy())
        
        except Exception as e:
            continue
    
    # Sonuçları işle
    n_ladder_all = len(sonuclar_ladder)
    n_full = len(sonuclar_full)
    n_ladder_only = n_ladder_all - n_full
    
    print(f"\n✅ Tarama tamamlandı!")
    print(f"📊 Sonuçlar:")
    print(f"  • Merdiven + Yeşil (Tüm): {n_ladder_all} hisse")
    print(f"  • Merdiven + Yeşil + SMA({sma_period}) Üstü: {n_full} hisse")
    print(f"  • Sadece Merdiven + Yeşil (SMA olmadan): {n_ladder_only} hisse")
    
    # Telegram mesajı hazırla
    tarih_saat = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    message = f"""<b>🔔 Merdiven Hacim Taraması</b>\n\n
📅 Tarih: {tarih_saat}
📊 Periyot: {interval_label}
⏳ SMA: {sma_period} bar\n\n
<b>📈 Sonuçlar:</b>
🎯 Merdiven + Yeşil (Tüm): {n_ladder_all} hisse
✅ Merdiven + Yeşil + SMA Üstü: {n_full} hisse
🔎 Sadece Merdiven (SMA olmadan): {n_ladder_only} hisse\n\n"""
    
    # Full listesini ekle
    if n_full > 0:
        message += "<b>✨ En Güçlü Sinyaller (SMA Üstü):</b>\n"
        for i, row in enumerate(sonuclar_full[:10], 1):  # İlk 10 hisse
            message += f"{i}. <code>{row['Hisse']}</code> - Hacim: {row['Son Hacim']:,}\n"
        if n_full > 10:
            message += f"\n... ve {n_full - 10} hisse daha\n"
    
    # Telegram'a gönder
    send_telegram_message(message)
    
    print(f"\n✅ İşlem tamamlandı: {tarih_saat}")

if __name__ == "__main__":
    main()

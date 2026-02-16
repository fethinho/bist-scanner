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
# from tradingview_screener import get_all_symbols
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
# BIST hisseleri - Scanner.py dosyasından alınacak
    try:
        from scanner_15m import get_bist_stocks
        hisseler = sorted(get_bist_stocks())
    except:
        # Fallback: Temel BIST30 hisseleri
        hisseler = sorted(['AKBNK', 'ARCLK', 'ASELS', 'BIMAS', 'EREGL', 'FROTO', 'GARAN', 
                          'HALKB', 'ISCTR', 'KCHOL', 'KOZAL', 'KOZAA', 'KRDMD', 'MGROS', 
                          'PETKM', 'PGSUS', 'SAHOL', 'SASA', 'SISE', 'TAVHL', 'TCELL', 
                          'THYAO', 'TKFEN', 'TOASO', 'TTKOM', 'TUPRS', 'VAKBN', 'VESTL', 
                          'YKBNK', 'AKSA', 'ALARK', 'ALGYO', 'ANACM', 'ANELE', 'ASTOR', 
                          'AYDEM', 'AYEN', 'AYGAZ', 'BAGFS', 'BJKAS', 'BRISA', 'BRSAN', 
                          'BUCIM', 'CASA', 'CCOLA', 'CLEBI', 'CIMSA', 'DOAS', 'ECILC', 
                          'EGEEN', 'EKGYO', 'ENKAI', 'ENJSA', 'FENER', 'GESAN', 'GOODY', 
                          'GUBRF', 'GOZDE', 'IEYHO', 'IMASM', 'INDES', 'IPEKE', 'ISMEN', 
                          'IZMDC', 'KARTN', 'KLKIM', 'KMPUR', 'KONTR', 'KONYA', 'KORDS', 
                          'KOZGR', 'LOGO', 'MAVI', 'MPARK', 'NETAS', 'NTTUR', 'ODAS', 
                          'OTKAR', 'OYAKC', 'PARSN', 'PENTA', 'PRKME', 'QUAGR', 'REEDR', 
                          'RTALB', 'SMRTG', 'SOKM', 'SNGYO', 'TBORG', 'TMSN', 'TRGYO', 
                          'TRILC', 'TSKB', 'TTRAK', 'ULKER', 'VESBE', 'YATAS', 'YEOTK', 
                          'ZOREN'])

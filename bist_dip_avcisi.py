import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.momentum import RSIIndicator
import warnings
import os

warnings.filterwarnings("ignore")

# ============================================================
# MONEY TRADER DİP AVCISI - BIST TARAMA
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8792118863:AAFvpNIuJ5nRipxe3oHIVHkx4gIhhWuqUjA')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '314746106')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Message sent to Telegram successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

# BIST hisse listesi
bist_symbols = [
    'ACSEL', 'ADEL', 'ADESE', 'ADGYO', 'AEFES', 'AFYON', 'AGESA', 'AGHOL', 'AGROT', 'AGYO',
    'AHGAZ', 'AKBNK', 'AKCNS', 'AKFGY', 'AKGRT', 'AKGUV', 'AKMGY', 'AKSA', 'AKSEN', 'AKSGY',
    'AKSUE', 'AKTIF', 'ALARK', 'ALCAR', 'ALFAS', 'ALGYO', 'ALKA', 'ALKIM', 'ALKLC', 'ALMAD',
    'ALTINS', 'ALVES', 'ANELE', 'ANGEN', 'ANHYT', 'ANSGR', 'ARASE', 'ARCLK', 'ARDYZ', 'ARENA',
    'ARSAN', 'ARTMS', 'ARZUM', 'ASELS', 'ASGYO', 'ASTOR', 'ASUZU', 'ATAKP', 'ATATP', 'ATEKS',
    'ATLAS', 'ATSYH', 'AVGYO', 'AVHOL', 'AVOD', 'AVPGY', 'AVTUR', 'AYCES', 'AYEN', 'AYGAZ',
    'AZTEK', 'BAGFS', 'BAHKM', 'BAKAB', 'BALSU', 'BANVT', 'BARMA', 'BASCM', 'BASGZ', 'BAYRK',
    'BERA', 'BEYAZ', 'BFREN', 'BIENY', 'BIGCH', 'BIMAS', 'BINBN', 'BIOEN', 'BIZIM', 'BJKAS',
    'BKFIN', 'BLCYT', 'BMEKS', 'BNTAS', 'BOBET', 'BOORV', 'BORSK', 'BOSSA', 'BRISA', 'BRKO',
    'BRKSN', 'BRKVY', 'BRSAN', 'BRYAT', 'BSOKE', 'BTCIM', 'BUCIM', 'BUFIN', 'BURCE', 'BURVA',
    'BVSAN', 'BYDNR', 'CAKMK', 'CANTE', 'CARGO', 'CASA', 'CCOLA', 'CELHA', 'CEMAS', 'CEMTS',
    'CEOEM', 'CIMSA', 'CLEBI', 'CMBTN', 'CMENT', 'CONSE', 'COSMO', 'CRDFA', 'CRFSA', 'CUSAN',
    'CVKMD', 'CWENE', 'DAGHL', 'DAGI', 'DAPGM', 'DARDL', 'DENGE', 'DERHL', 'DESA', 'DESPC',
    'DEVA', 'DGATE', 'DGGYO', 'DGNMO', 'DITAS', 'DMRGD', 'DMSAS', 'DNISI', 'DOAS', 'DOBUR',
    'DOCO', 'DOGUB', 'DOHOL', 'DOKTA', 'DURDO', 'DYOBY', 'DZGYO', 'EBEBK', 'ECILC', 'ECZYT',
    'EDIP', 'EGEGY', 'EGGUB', 'EGPRO', 'EGSER', 'EKGYO', 'EKIZ', 'EKOS', 'EKSUN', 'ELITE',
    'EMKEL', 'EMNIS', 'ENERY', 'ENGYO', 'ENKAI', 'ENPLA', 'ENTRA', 'EPLAS', 'ERBOS', 'ERCB',
    'EREGL', 'ERSU', 'ESCAR', 'ESCOM', 'ESEN', 'ETILR', 'ETYAT', 'EUHOL', 'EUREN', 'EUYO',
    'EYGYO', 'FADE', 'FENER', 'FLAP', 'FMIZP', 'FONET', 'FORMT', 'FORTE', 'FROTO', 'FZLGY',
    'GARAN', 'GARFA', 'GEDIK', 'GEDZA', 'GEMAS', 'GEREL', 'GESAN', 'GLYHO', 'GMTAS', 'GOKNR',
    'GOLTS', 'GOODY', 'GOZDE', 'GRSEL', 'GRTHO', 'GRTRK', 'GUBRF', 'GWIND', 'GZNMI', 'HALKB',
    'HATEK', 'HDFGS', 'HEDEF', 'HEKTS', 'HKTM', 'HLGYO', 'HOROZ', 'HRKET', 'HTTBT', 'HUBVC',
    'HUNER', 'HURGZ', 'ICBCT', 'ICUGS', 'IDEAS', 'IDGYO', 'IEYHO', 'IHAAS', 'IHEVA', 'IHLGM',
    'IHYAY', 'IMASM', 'INDES', 'INFO', 'INGRM', 'INTEM', 'INVEO', 'INVES', 'IPEKE', 'ISATR',
    'ISBIR', 'ISCTR', 'ISFIN', 'ISGSY', 'ISGYO', 'ISKPL', 'ISKUR', 'ISMEN', 'ISSEN', 'ISYAT',
    'ITFAQ', 'IZENR', 'IZFAS', 'IZINV', 'IZMDC', 'JANTS', 'KAPLM', 'KAREL', 'KARSN', 'KARTN',
    'KARYE', 'KATMR', 'KAYSE', 'KBORU', 'KCAER', 'KCHOL', 'KENT', 'KERVN', 'KERVT', 'KFEIN',
    'KGYO', 'KIMMR', 'KIPA', 'KLGYO', 'KLKIM', 'KLMSN', 'KLNMA', 'KLRHO', 'KLSER', 'KMPUR',
    'KNFRT', 'KONAK', 'KONTR', 'KONYA', 'KOPOL', 'KORDS', 'KOZAA', 'KOZAL', 'KRDMA', 'KRDMB',
    'KRDMD', 'KRGYO', 'KRONT', 'KRPLS', 'KRSTL', 'KRTEK', 'KSTUR', 'KTLEV', 'KTSKR', 'KUCUK',
    'KUYAS', 'KZBGY', 'KZGYO', 'LIDER', 'LIDFA', 'LINK', 'LKMNH', 'LMKDC', 'LOGO', 'LRSHO',
    'LUKSK', 'LYKHO', 'LYDYE', 'MAALT', 'MACKO', 'MAGEN', 'MAKIM', 'MANAS', 'MARBL', 'MARKA',
    'MARTI', 'MAVI', 'MEDTR', 'MEGAP', 'MEKAG', 'MERIM', 'MERKO', 'METRO', 'METUR', 'MGROS',
    'MHRGY', 'MIATK', 'MICAP', 'MILFA', 'MIPAZ', 'MMCAS', 'MNDRS', 'MNDTR', 'MOBTL', 'MOGAN',
    'MORAM', 'MPARK', 'MRGYO', 'MRSHL', 'MSGYO', 'MTRKS', 'MTRYO', 'MZHLD', 'NATEN', 'NETAS',
    'NIBAS', 'NILYT', 'NKELU', 'NKHOME', 'NKOMD', 'NTHOL', 'NTTUR', 'NUGYO', 'NUHCM', 'OBAMS',
    'ODAS', 'ODINE', 'OFSYM', 'ONCSM', 'ONRYT', 'ORCAY', 'ORGE', 'ORMA', 'OSMEN', 'OSTIM',
    'OTKAR', 'OTTO', 'OYAKC', 'OYAYO', 'OYLUM', 'OYYAT', 'OZGYO', 'OZKGY', 'OZRDN', 'OZTKS',
    'PAGYO', 'PAMEL', 'PAPIL', 'PARSN', 'PASEU', 'PCILT', 'PEHOL', 'PEKGY', 'PENGD', 'PENTA',
    'PETKM', 'PETUN', 'PGSUS', 'PINSU', 'PKART', 'PKENT', 'PLTUR', 'PNLSN', 'POLHO', 'POLTK',
    'PRDGS', 'PRZMA', 'PSDTC', 'PSGYO', 'PTOFS', 'QNBFB', 'QNBFL', 'RALYH', 'RAYSG', 'REEDR',
    'RGYAS', 'RHEAG', 'RNPOL', 'RODRG', 'ROYAL', 'RUBNS', 'RYSAS', 'SAFKR', 'SAHOL', 'SAMAT',
    'SANEL', 'SANFM', 'SANKO', 'SARKY', 'SAYAS', 'SDTTR', 'SEGYO', 'SEKFK', 'SEKUR', 'SELGD',
    'SELVA', 'SEYKM', 'SILVR', 'SISE', 'SKBNK', 'SKTAS', 'SKYLP', 'SMART', 'SNGYO', 'SNKRN',
    'SODSN', 'SOKM', 'SONME', 'SRVGY', 'SUMAS', 'SUNTK', 'SURGY', 'SUWEN', 'TABGD', 'TATGD',
    'TAVHL', 'TBORG', 'TCELL', 'TDGYO', 'TEKTU', 'TERA', 'TETMT', 'TEZOL', 'TGSAS', 'THYAO',
    'TIRE', 'TKFEN', 'TKNSA', 'TLMAN', 'TOASO', 'TRCAS', 'TRGYO', 'TRILC', 'TSKB', 'TSPOR',
    'TTKOM', 'TTRAK', 'TUCLK', 'TUKAS', 'TUPRS', 'TUREX', 'TURGG', 'TURSG', 'UFUK', 'ULUFA',
    'ULUSE', 'ULUUN', 'UMPAS', 'UNLU', 'USAK', 'USDTR', 'UTPYA', 'UVITE', 'VANGD', 'VBTYZ',
    'VCspy', 'VEEZY', 'VERUS', 'VESBE', 'VESTL', 'VKFYO', 'VKING', 'VRGYO', 'WLMDI', 'YAPRK',
    'YATAS', 'YAYLA', 'YGYO', 'YKSLN', 'YONGA', 'YUNSA', 'YYAPI', 'ZEDUR', 'ZOREN', 'ZRGYO'
]

print("============================================================")
print("MONEY TRADER DİP AVCISI - BIST TARAMA")
print("============================================================")
print(f"Toplam {len(bist_symbols)} hisse taranıyor...")
print("============================================================")

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(f"{symbol}.IS")
        df = ticker.history(period="3mo", interval="1d")
        if df.empty or len(df) < 20:
            return None
        return df
    except Exception:
        return None

def calculate_buy_zone(df):
    recent = df.tail(20)
    support = recent['Low'].min()
    support2 = recent['Low'].nsmallest(3).mean()
    return support, support2

def analyze_stock(symbol):
    df = get_stock_data(symbol)
    if df is None:
        return None
    
    close = df['Close']
    volume = df['Volume']
    current_price = close.iloc[-1]
    
    rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
    
    avg_volume = volume.rolling(20).mean().iloc[-1]
    last_volume = volume.iloc[-1]
    vol_ratio = last_volume / avg_volume if avg_volume > 0 else 0
    
    buy_zone_low, buy_zone_high = calculate_buy_zone(df)
    buy_zone_high2 = buy_zone_high * 1.02
    
    # Dip bölgesi hesaplama
    recent_low = df['Low'].tail(10).min()
    recent_high = df['High'].tail(10).max()
    dip_zone_low = recent_low
    dip_zone_high = recent_low * 1.05
    
    is_buy_zone = buy_zone_low <= current_price <= buy_zone_high2
    is_dip_zone = rsi < 42 and current_price <= dip_zone_high
    is_strong_breakout = rsi > 50 and vol_ratio > 1.5
    
    # Dip dönüşü sinyali
    prev_rsi = RSIIndicator(close=close, window=14).rsi().iloc[-2] if len(close) > 15 else rsi
    is_dip_reversal = prev_rsi < 35 and rsi > prev_rsi and rsi < 45
    
    # Trend dönüşü
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else ma20
    is_trend_reversal = current_price > ma20 and close.iloc[-2] < ma20 and vol_ratio > 2
    
    return {
        'symbol': symbol,
        'price': round(current_price, 2),
        'rsi': round(rsi, 1),
        'vol_ratio': round(vol_ratio, 2),
        'buy_zone_low': round(buy_zone_low, 2),
        'buy_zone_high': round(buy_zone_high2, 2),
        'dip_zone_low': round(dip_zone_low, 2),
        'dip_zone_high': round(dip_zone_high, 2),
        'is_buy_zone': is_buy_zone,
        'is_dip_zone': is_dip_zone,
        'is_strong_breakout': is_strong_breakout,
        'is_dip_reversal': is_dip_reversal,
        'is_trend_reversal': is_trend_reversal
    }

results = []
for i, symbol in enumerate(bist_symbols):
    result = analyze_stock(symbol)
    if result:
        results.append(result)
    if (i + 1) % 50 == 0:
        print(f"{i+1}/{len(bist_symbols)} hisse tamamlandı...")

print(f"Toplam {len(results)} hisse başarıyla analiz edildi.")

df_result = pd.DataFrame(results)

dip_stocks = df_result[df_result['is_dip_zone'] == True]
buy_stocks = df_result[df_result['is_buy_zone'] == True]
kirilim_stocks = df_result[df_result['is_strong_breakout'] == True]
dip_donus = df_result[df_result['is_dip_reversal'] == True]
trend_donus = df_result[df_result['is_trend_reversal'] == True]

print("============================================================")
print(f"🟢 DİP BÖLGESİ'NDEKİ HİSSELER ({len(dip_stocks)} hisse)")
print("============================================================")
if len(dip_stocks) > 0:
    print(dip_stocks[['symbol','price','rsi','vol_ratio','buy_zone_low','buy_zone_high','dip_zone_low','dip_zone_high']].to_string(index=False))

print("============================================================")
print(f"✅ BUY ZONE'DAKİ HİSSELER ({len(buy_stocks)} hisse)")
print("============================================================")
if len(buy_stocks) > 0:
    print(buy_stocks[['symbol','price','rsi','vol_ratio','buy_zone_low','buy_zone_high']].to_string(index=False))

print("============================================================")
print(f"⚡ GÜÇLÜ KIRILIM SİNYALLERİ ({len(kirilim_stocks)} hisse)")
print("============================================================")
if len(kirilim_stocks) > 0:
    print(kirilim_stocks[['symbol','price','rsi','vol_ratio']].to_string(index=False))
else:
    print("Sinyal yok.")

print("============================================================")
print(f"🟢 DİP DÖNÜŞÜ SİNYALLERİ ({len(dip_donus)} hisse)")
print("============================================================")
if len(dip_donus) > 0:
    print(dip_donus[['symbol','price','rsi','vol_ratio']].to_string(index=False))
else:
    print("Sinyal yok.")

print("============================================================")
print(f"🟠 TREND DÖNÜŞÜ (MAJOR KIRILIM) ({len(trend_donus)} hisse)")
print("============================================================")
if len(trend_donus) > 0:
    print(trend_donus[['symbol','price','rsi','vol_ratio']].to_string(index=False))
else:
    print("Sinyal yok.")

df_result.to_csv('bist_dip_avcisi_sonuclar.csv', index=False)
print("💾 Tüm sonuçlar 'bist_dip_avcisi_sonuclar.csv' dosyasına kaydedildi.")

# ============================================================
# TELEGRAM BİLDİRİMLERİ
# ============================================================
import datetime
tr_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
time_str = tr_time.strftime('%d.%m.%Y %H:%M')

telegram_summary = f"""
*📊 BIST DİP AVCISI TARAMA - {time_str}*

*✅ Analiz edilen hisse:* {len(df_result)} hisse
*🟢 Dip Bölgesi'nde:* {len(dip_stocks)} hisse
*✅ Buy Zone'da:* {len(buy_stocks)} hisse
*⚡ Güçlü Kırılım:* {len(kirilim_stocks)} hisse
*🟢 Dip Dönüşü:* {len(dip_donus)} hisse
*🟠 Trend Dönüşü:* {len(trend_donus)} hisse
"""
send_telegram_message(telegram_summary)

# Dip bölgesi hisselerini gönder
if len(dip_stocks) > 0:
    dip_msg = "*🟢 DİP BÖLGESİ HİSSELERİ:*\n"
    for _, row in dip_stocks.iterrows():
        dip_msg += f"• *{row['symbol']}* | Fiyat: {row['price']} | RSI: {row['rsi']}\n"
    send_telegram_message(dip_msg)

# Buy zone hisselerini gönder
if len(buy_stocks) > 0:
    buy_msg = "*✅ BUY ZONE HİSSELERİ:*\n"
    for _, row in buy_stocks.iterrows():
        buy_msg += f"• *{row['symbol']}* | Fiyat: {row['price']} | RSI: {row['rsi']}\n"
    send_telegram_message(buy_msg)

# Kırılım sinyalleri
if len(kirilim_stocks) > 0:
    kir_msg = "*⚡ GÜÇLÜ KIRILIM SİNYALLERİ:*\n"
    for _, row in kirilim_stocks.iterrows():
        kir_msg += f"• *{row['symbol']}* | Fiyat: {row['price']} | RSI: {row['rsi']} | Hacim: {row['vol_ratio']}x\n"
    send_telegram_message(kir_msg)

print("\n✅ Tüm Telegram mesajları gönderildi.")

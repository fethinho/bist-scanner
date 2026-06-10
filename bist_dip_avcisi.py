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
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik, mesaj gönderilemiyor.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("✅ Telegram mesajı başarıyla gönderildi!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram mesajı gönderilemedi: {e}")

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
    'VCSPY', 'VEEZY', 'VERUS', 'VESBE', 'VESTL', 'VKFYO', 'VKING', 'VRGYO', 'WLMDI', 'YAPRK',
    'YATAS', 'YAYLA', 'YGYO', 'YKSLN', 'YONGA', 'YUNSA', 'YYAPI', 'ZEDUR', 'ZOREN', 'ZRGYO'
]

print("============================================================")
print("MONEY TRADER DİP AVCISI - BIST TARAMA")
print("============================================================")
print(f"Toplam {len(bist_symbols)} hisse taranıyor...")
print("============================================================\n")

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
    if df is None or len(df) < 60:
        return None

    close = df['Close']
    high = df['High']
    low = df['Low']
    open_ = df['Open']
    volume = df['Volume']

    current_price = close.iloc[-1]
    prev_close = close.iloc[-2]

    rsi_series = RSIIndicator(close=close, window=14).rsi()
    rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]
    prev2_rsi = rsi_series.iloc[-3]

    avg_volume = volume.rolling(20).mean().iloc[-1]
    last_volume = volume.iloc[-1]
    vol_ratio = last_volume / avg_volume if avg_volume and avg_volume > 0 else 0

    ma10 = close.rolling(10).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    ma20_prev = close.rolling(20).mean().iloc[-2]
    ma50_prev = close.rolling(50).mean().iloc[-2]

    buy_zone_low, buy_zone_high = calculate_buy_zone(df)
    buy_zone_high2 = buy_zone_high * 1.02

    recent_low_10 = low.tail(10).min()
    recent_low_5 = low.tail(5).min()
    recent_high_10 = high.tail(10).max()

    dip_zone_low = recent_low_10
    dip_zone_high = recent_low_10 * 1.05

    is_buy_zone = buy_zone_low <= current_price <= buy_zone_high2
    is_dip_zone = (rsi < 42) and (current_price <= dip_zone_high)
    is_strong_breakout = (rsi > 55) and (vol_ratio > 1.7) and (current_price > ma20)

    bullish_candle = current_price > open_.iloc[-1]
    near_recent_dip = current_price <= recent_low_10 * 1.08
    rsi_recovering = (prev_rsi < 35) and (rsi > prev_rsi) and (rsi > prev2_rsi)
    price_reclaim = current_price > prev_close
    volume_confirm = vol_ratio > 1.10

    is_dip_reversal = (
        near_recent_dip
        and rsi_recovering
        and bullish_candle
        and price_reclaim
        and volume_confirm
    )

    ma20_rising = ma20 > ma20_prev
    ma50_rising = ma50 >= ma50_prev
    crossed_ma20 = (prev_close < ma20_prev) and (current_price > ma20)
    above_ma50 = current_price > ma50
    breakout_10d = current_price > high.tail(10).iloc[:-1].max()
    strong_trend_volume = vol_ratio > 1.30

    is_trend_reversal = (
        crossed_ma20
        and above_ma50
        and ma20_rising
        and ma50_rising
        and strong_trend_volume
        and rsi > 50
    )

    return {
        'symbol': symbol,
        'price': round(current_price, 2),
        'rsi': round(rsi, 1),
        'vol_ratio': round(vol_ratio, 2),
        'buy_zone_low': round(buy_zone_low, 2),
        'buy_zone_high': round(buy_zone_high2, 2),
        'dip_zone_low': round(dip_zone_low, 2),
        'dip_zone_high': round(dip_zone_high, 2),
        'ma10': round(ma10, 2),
        'ma20': round(ma20, 2),
        'ma50': round(ma50, 2),
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

print(f"\nToplam {len(results)} hisse başarıyla analiz edildi.\n")
df_result = pd.DataFrame(results)

dip_stocks = df_result[df_result['is_dip_zone'] == True]
buy_stocks = df_result[df_result['is_buy_zone'] == True]
kirilim_stocks = df_result[df_result['is_strong_breakout'] == True]
dip_donus = df_result[df_result['is_dip_reversal'] == True]
trend_donus = df_result[df_result['is_trend_reversal'] == True]

print("============================================================")
print(f"🟢 DİP DÖNÜŞÜ SİNYALLERİ ({len(dip_donus)} hisse)")
print("============================================================")
if len(dip_donus) > 0:
    print(dip_donus[['symbol','price','rsi','vol_ratio']].to_string(index=False))
else:
    print("Sinyal yok.")

print("\n============================================================")
print(f"🟠 TREND DÖNÜŞÜ SİNYALLERİ ({len(trend_donus)} hisse)")
print("============================================================")
if len(trend_donus) > 0:
    print(trend_donus[['symbol','price','rsi','vol_ratio']].to_string(index=False))
else:
    print("Sinyal yok.")

df_result.to_csv('bist_dip_avcisi_sonuclar.csv', index=False)
print("\n💾 Tüm sonuçlar 'bist_dip_avcisi_sonuclar.csv' dosyasına kaydedildi.")

# ============================================================
# TELEGRAM BİLDİRİMLERİ - SADECE DİP VE TREND DÖNÜŞÜ
# ============================================================
import datetime

tr_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
time_str = tr_time.strftime('%d.%m.%Y %H:%M')

telegram_summary = f"""
*📊 BIST DİP AVCISI TARAMA - {time_str}*

*🟢 Dip Dönüşü:* {len(dip_donus)} hisse
*🟠 Trend Dönüşü:* {len(trend_donus)} hisse
"""
send_telegram_message(telegram_summary)

if len(dip_donus) > 0:
    dip_donus_msg = "*🟢 DİP DÖNÜŞÜ SİNYALLERİ:*\n"
    for _, row in dip_donus.sort_values(["vol_ratio", "rsi"], ascending=[False, True]).iterrows():
        dip_donus_msg += (
            f"• *{row['symbol']}* | "
            f"Fiyat: {row['price']} | "
            f"RSI: {row['rsi']} | "
            f"Hacim: {row['vol_ratio']}x\n"
        )
    send_telegram_message(dip_donus_msg)
else:
    send_telegram_message("*🟢 DİP DÖNÜŞÜ SİNYALLERİ:* Sinyal yok.")

if len(trend_donus) > 0:
    trend_donus_msg = "*🟠 TREND DÖNÜŞÜ SİNYALLERİ:*\n"
    for _, row in trend_donus.sort_values(["vol_ratio", "rsi"], ascending=[False, False]).iterrows():
        trend_donus_msg += (
            f"• *{row['symbol']}* | "
            f"Fiyat: {row['price']} | "
            f"RSI: {row['rsi']} | "
            f"Hacim: {row['vol_ratio']}x\n"
        )
    send_telegram_message(trend_donus_msg)
else:
    send_telegram_message("*🟠 TREND DÖNÜŞÜ SİNYALLERİ:* Sinyal yok.")

print("\n✅ Sadece dip dönüşü ve trend dönüşü Telegram mesajları gönderildi.")

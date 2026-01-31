# BIST Hisse Senedi Tarayıcı 📊

Otomatik BIST (Borsa İstanbul) hisse senedi tarayıcısı. 15 dakikalık periyotta teknik analiz yaparak sinyalleri Telegram'a gönderir.

## Özellikler ✨

- 📈 15 dakikalık periyotta otomatik tarama
- 🤖 Telegram bot entegrasyonu
- 📊 RSI ve SMA20 göstergeleri
- ⏰ Zamanlanmış otomatik çalışma (Hafta içi 09:56)
- 🇹🇷 UTC+3 saat dilimi desteği

## Kurulum 🛠️

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/fethinho/bist-scanner.git
cd bist-scanner
```

### 2. Gerekli Kütüphaneleri Yükleyin

```bash
pip install -r requirements.txt
```

## Manuel Çalıştırma 🚀

Scripti manuel olarak çalıştırmak için:

```bash
python bist_scanner_auto.py
```

## Otomatik Zamanlama ⏰

### Windows Task Scheduler ile Otomatik Çalıştırma

1. **Task Scheduler'ı açın** (Başlat → "Task Scheduler" yazın)

2. **Create Basic Task** seçeneğine tıklayın

3. **Görev Ayarları:**
   - Name: "BIST Scanner 15m"
   - Trigger: Daily (Günlük)
   - Start time: 09:56 (Türkiye saati UTC+3)
   - Action: Start a program
   - Program/script: `python`
   - Add arguments: `C:\path\to\bist_scanner_auto.py`
   - Start in: `C:\path\to\bist-scanner`

4. **Hafta içi çalışması için:**
   - Görev oluşturulduktan sonra sağ tık → Properties
   - Triggers sekmesinde → Edit
   - "Weekly" seçin ve sadece Pazartesi-Cuma işaretleyin

### Linux/Mac Cron Job ile Otomatik Çalıştırma

1. Cron editörünü açın:
```bash
crontab -e
```

2. Aşağıdaki satırı ekleyin (Pazartesi-Cuma 09:56'da çalışır):
```bash
56 9 * * 1-5 cd /path/to/bist-scanner && /usr/bin/python3 bist_scanner_auto.py
```

## Telegram Bot Kurulumu 🤖

Script zaten yapılandırılmış Telegram bot bilgilerini içeriyor:
- Bot Token: 8460458441:AAG81QuP0nDc0AT5SYON63bus2d0udab0Iw
- Chat ID: 314746106

## Teknik Detaylar 🔧

### Sinyal Koşulları

**AL Sinyali (🟢):**
- RSI < 30 (Aşırı satım bölgesi)
- Fiyat > SMA20 (Destek üzerinde)

**SAT Sinyali (🔴):**
- RSI > 70 (Aşırı alım bölgesi)
- Fiyat < SMA20 (Direnç altında)

### Taranan Hisseler

30 BIST hissesi taranmaktadır:
THYAO, ASELS, EREGL, SISE, KCHOL, SAHOL, AKBNK, TUPRS, VAKBN, ISCTR, GARAN, TTKOM, TAVHL, ENKAI, PETKM, KOZAL, KOZAA, BIMAS, ARCLK, EKGYO, HEKTS, KRDMD, FROTO, TOASO, TCELL, VESTL, PGSUS, AEFES, DOHOL, ODAS

## Notlar 📝

- Script hafta içi her gün saat 09:56'da çalışacak şekilde ayarlanmalıdır
- İnternet bağlantısı gereklidir
- Telegram bildirimleri gerçek zamanlı gönderilir
- PC'nin açık olması gerekmektedir (VPS kullanılması önerilir)

## Sorun Giderme 🔍

**Script çalışmıyor mu?**
1. Python versiyonunu kontrol edin: `python --version` (Python 3.8+)
2. Kütüphanelerin yüklü olduğundan emin olun: `pip list`
3. İnternet bağlantısını kontrol edin
4. Telegram bot token ve chat ID'yi kontrol edin

## Lisans 📄

Bu proje açık kaynaklıdır ve özgürce kullanılabilir.

---

**Not:** Yatırım kararlarınızı verirken lütfen profesyonel danışmanlık alın. Bu araç sadece teknik analiz sinyalleri sağlar.

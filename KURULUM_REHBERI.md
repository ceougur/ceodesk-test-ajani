# CEODESK Test + İzleme Ajanı — Kurulum Rehberi

Bu rehber hiç kod bilmediğini varsayarak yazıldı. Her adımı sırayla takip et.

## Bu ajan ne yapıyor, ne yapmıyor?

**Yapıyor**: GitHub'ın kendi ücretsiz zamanlayıcısı (GitHub Actions) her 20
dakikada bir (ayarlanabilir) siteni gerçek bir tarayıcıyla ziyaret edip
gerçek bir oyuncu gibi test eder — anasayfa, giriş, Tedarik Zinciri, Market
API, `/admin` ve `/op` sayfaları. Bir sorun bulursa (konsol hatası, sunucu
hatası, beklenmeyen davranış) sana **Telegram'dan** mesaj + varsa ekran
görüntüsü gönderir. Ayrıca Vercel'deki en son deployment'ın durumunu
izler, build hatası olursa haber verir.

**YAPMIYOR (bilinçli olarak)**: Kodu kendi kendine değiştirmiyor, GitHub'a
otomatik push/merge yapmıyor, canlı siteyi otomatik güncellemiyor. Bu,
konuştuğumuz güvenlik nedeniyle bilinçli bir tercih — sitende gerçek
oyuncu hesapları ve verisi olduğu için, kod değişikliklerinin gerçek bir
GitHub PR incelemesinden geçmesi gerekiyor.

## Mimari notu: neden Render değil, GitHub Actions?

İlk planımız Render.com'du, ama kurulum sırasında Render'ın "Background
Worker" (7/24 arka planda çalışan süreç) hizmetinde **ücretsiz katman
olmadığını** keşfettik — en ucuz plan bile 7$/ay. Bunun yerine tamamen
ücretsiz bir yaklaşıma geçtik: **GitHub Actions**. Fark şu: ajan artık
sürekli açık bir sunucuda beklemiyor — GitHub, zamanı geldiğinde (cron ile,
her 20 dakikada bir) taze bir makine açıp botu **bir kez** çalıştırıp
kapatıyor. Sonuç senin için aynı (düzenli test + Telegram bildirimi),
maliyet sıfır. Deponun **herkese açık (public)** olması sayesinde GitHub
Actions dakikaları tamamen sınırsız ve ücretsiz.

## Genel bakış — sırayla ne yapacaksın

1. Telegram bot oluştur ✅ (tamamlandı)
2. Test için ayrı bir oyun hesabı belirle ve **tek seferlik** manuel kurulum yap ✅ (tamamlandı)
3. Kodu GitHub'a yükle ✅ (tamamlandı)
4. GitHub deposunda "Secrets" (gizli değerler) ekle — **sıradaki adım bu**
5. Doğrula: Telegram'a "Ajan başlatıldı" mesajı gelmeli

---

## Adım 4 — GitHub Secrets Ekle

Bu, gerçek şifre/token gibi bilgilerin koda hiç yazılmadan, güvenli
şekilde GitHub Actions'a ulaşmasını sağlıyor.

1. `ceodesk-test-ajani` deposuna git.
2. Üstteki **Settings** (Ayarlar) sekmesine tıkla.
3. Sol menüden **Secrets and variables** → **Actions**'a tıkla.
4. **New repository secret** butonuna bas. Aşağıdaki her satır için bunu
   tekrarla (isim ve değeri aynen kopyala-yapıştır):

| Secret adı | Değer |
|---|---|
| `SITE_URL` | `https://ceonun-masasi.vercel.app` |
| `TEST_COMPANY_NAME` | `TestAjan1` |
| `TEST_COMPANY_PASSWORD` | (kurarken seçtiğin şifre) |
| `TELEGRAM_BOT_TOKEN` | BotFather'dan aldığın token |
| `TELEGRAM_CHAT_ID` | getUpdates'ten bulduğun sayı |

Aşağıdakiler **isteğe bağlı** — eklemesen de ajan çalışır, sadece o
kısımlar (admin girişi testi / Vercel izleme) devre dışı kalır:
`ADMIN_PANEL_SECRET`, `VERCEL_API_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_PROJECT_ID`.

## Adım 5 — Doğrula

1. Depo sayfasında üstteki **Actions** sekmesine git.
2. Sol tarafta "CEODESK Test Ajanı" adlı workflow'u göreceksin. Üzerine tıkla.
3. Sağ üstte **Run workflow** butonuyla ilk çalıştırmayı elle tetikleyebilirsin
   (yoksa ilk otomatik çalıştırma için en fazla 20 dakika beklemen gerekir).
4. 1-2 dakika içinde Telegram'a şu mesaj gelmeli:

   > 🟢 **CEODESK Test Ajanı başlatıldı.**
   > Arka planda çalışıyor, siteyi periyodik olarak test edecek.

5. Actions sekmesindeki çalıştırmanın yanında yeşil ✓ (başarılı) ya da
   kırmızı ✗ (hata) işareti görünür — tıklayıp detaylı logları
   okuyabilirsin.

Gelmezse **Actions** sekmesindeki son çalıştırmanın loglarına bak, hata
mesajı orada görünecektir (çoğunlukla eksik/yanlış bir Secret'tır).

---

## Sık Sorulan Sorular

**"Ajan bir hata bulursa ne olur?"**
Telegram'a hatanın ne olduğunu, hangi test adımında bulunduğunu ve varsa
bir ekran görüntüsünü gönderir. Kodu KENDİSİ değiştirmez.

**"Test sıklığını değiştirmek istiyorum."**
`.github/workflows/test-agent.yml` dosyasını aç, `cron: '*/20 * * * *'`
satırındaki `20`'yi istediğin dakikayla değiştir (GitHub 5 dakikanın
altına inmeyi önermiyor). GitHub web arayüzünden dosyayı düzenleyip
"Commit changes" demen yeterli, kod bilmene gerek yok.

**"Ayarları (Secret'ları) sonradan değiştirebilir miyim?"**
Evet — Settings → Secrets and variables → Actions'tan ilgili secret'ın
yanındaki kalem ikonuna tıklayıp güncelle.

**"Botu geçici olarak durdurmak istiyorum."**
`.github/workflows/test-agent.yml` dosyasındaki `on:` bloğunun altına
`schedule:` satırının başına `#` koyup yorum satırı yapabilirsin — ya da
Actions sekmesinden workflow'u "Disable workflow" ile kapatabilirsin
(sağ üstteki "..." menüsü).

**"Sonraki aşama (otomatik düzeltme/self-healing) ne zaman?"**
İstediğinde söyle — GitHub PR + Vercel önizleme linki + Telegram bildirimi
üretecek ama canlıya almayı SENİN GitHub'da "Merge" tıklamana bırakacak
şekilde, konuştuğumuz güvenli tasarımla ekleyebilirim.

## Bilinen bulgu (test sırasında yakalandı, bilgin olsun)

Yeni kayıt olan bir hesap, kayıttan hemen sonraki birkaç saniye içinde ara
sıra yanlışlıkla "Hesap silindi" ekranına düşebiliyor, sayfa yenilenince
kendiliğinden düzeliyor. Test botu bunu algılayıp bir kez yeniden deniyor,
kalıcıysa net şekilde raporluyor. Bunun oyun tarafındaki kök nedenini
istersen ayrıca birlikte bulup düzeltebiliriz.

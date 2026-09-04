# CEODESK Test + İzleme Ajanı — Kurulum Rehberi

Bu rehber hiç kod bilmediğini varsayarak yazıldı. Her adımı sırayla takip et.

## Bu ajan ne yapıyor, ne yapmıyor?

**Yapıyor**: 7/24 arka planda çalışır (Render.com'da, ücretsiz), her 20
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
GitHub PR incelemesinden geçmesi gerekiyor. Bu "self-healing/otomatik
düzeltme" katmanı, istersen ayrı bir aşamada, yine bu güvenli tasarımla
eklenebilir.

## Genel bakış — sırayla ne yapacaksın

1. Telegram bot oluştur (5 dakika)
2. Test için ayrı bir oyun hesabı belirle ve **tek seferlik** manuel kurulum yap (2 dakika)
3. (İsteğe bağlı) Vercel API token'ı al (3 dakika)
4. Kodu GitHub'a yükle (5 dakika)
5. Render.com'da arka plan işçisi (Background Worker) olarak dağıt (5 dakika)
6. Doğrula: Telegram'a "Ajan başlatıldı" mesajı gelmeli

---

## Adım 1 — Telegram Bot Oluştur (ücretsiz, onay gerektirmez)

1. Telefonunda/bilgisayarında Telegram'ı aç, **@BotFather** hesabını ara (mavi onay işaretli resmi hesap).
2. BotFather'a `/newbot` yaz.
3. Botun için bir isim sor (görünen ad, örn. "CEODESK Test Ajanı").
4. Botun için bir kullanıcı adı iste — `bot` ile bitmesi zorunlu (örn. `ceodesk_test_bot`).
5. BotFather sana şuna benzer bir satır verecek:
   ```
   Use this token to access the HTTP API:
   123456789:AAExampleTokenHereXXXXXXXXXXXXXXXXXXX
   ```
   Bu, senin **TELEGRAM_BOT_TOKEN** değerin. Kopyala, bir kenara not et.
6. Şimdi kendi Chat ID'ni öğrenmen gerekiyor (botun mesajı SANA göndermesi için):
   - Telegram'da yeni oluşturduğun botu bul, ona **herhangi bir mesaj** gönder (örn. "merhaba").
   - Tarayıcında şu adrese git (BOT_TOKEN yerine kendi token'ını yapıştır):
     `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
   - Dönen JSON içinde `"chat":{"id":123456789,...}` gibi bir kısım göreceksin. O sayı senin **TELEGRAM_CHAT_ID**'n.

## Adım 2 — Test Hesabı ve Tek Seferlik Manuel Kurulum

Ajan, siteyi test ederken GERÇEK işlemler yapar (hammadde satın alır,
ekranları açar) — bu yüzden **kendi asıl oyun hesabını değil, ayrı bir test
hesabı** kullanmalısın.

1. `.env.example` dosyasındaki `TEST_COMPANY_NAME` ve `TEST_COMPANY_PASSWORD`
   değerlerini kendi seçtiğin, **5-10 karakter arası** bir isim/şifreyle
   değiştir (örn. `TestAjan1` / `TstPar123`).
2. **Tek seferlik manuel adım (önemli)**: `https://ceonun-masasi.vercel.app`
   adresine git, bu isim ve şifreyle **bir kez** normal şekilde "CEO
   Koltuğuna Otur" ile şirket kur (tıpkı yeni bir oyuncu gibi).
   - Bunu neden ajan kendisi otomatik yapmıyor? Test ederken bunu
     otomatikleştirmeyi denedim; oyunun kuruluş ekranı eski bir üyelik
     sisteminin (Clerk) kalıntısıyla iç içe olduğu için güvenilir şekilde
     otomatikleştirilemedi. Senin yapman 30 saniye sürer, sonrasında ajan
     bu hesapla **her zaman otomatik** giriş yapacak.
3. Bu adımdan sonra `.env` dosyana (`.env.example`'ı kopyalayıp) doğru
   isim/şifreyi yaz.

**Bilinen bulgu** (test sırasında yakaladım, bilgin olsun): yeni kayıt
olan bir hesap, kayıt olduktan hemen sonraki birkaç saniye içinde ara sıra
yanlışlıkla "Hesap silindi" ekranına düşebiliyor, kendiliğinden düzeliyor
(sayfa yenilenince kayboluyor). Test botu bunu algılayıp tek seferlik
yeniden deneme yapıyor, kalıcıysa sana bildiriyor. Bunun kök nedenini
(muhtemelen kayıt sonrası erişim kontrolüyle ilgili bir zamanlama meselesi)
istersen ayrı bir konuşmada birlikte araştırıp düzeltebiliriz.

## Adım 3 — (İsteğe Bağlı) Vercel API Token'ı

Bu adımı atlarsan sorun değil — sadece Vercel deployment durumu izlemesi
devre dışı kalır, oyun testleri yine çalışır.

1. https://vercel.com/account/tokens adresine git.
2. "Create Token" — bir isim ver (örn. "ceodesk-test-ajani"), süresi
   sınırsız ya da 1 yıl seçebilirsin.
3. Oluşan token'ı kopyala — bu **VERCEL_API_TOKEN**'ın (bir daha
   gösterilmez, kaybedersen yeni bir tane oluşturman gerekir).
4. `VERCEL_TEAM_ID` ve `VERCEL_PROJECT_ID` için `.env.example` dosyasında
   zaten projenin doğru değerlerini önceden doldurdum, değiştirmene
   gerek yok.

## Adım 4 — Kodu GitHub'a Yükle

1. GitHub'da yeni, **boş ve gizli (private)** bir depo oluştur, örn.
   `ceodesk-test-ajani`.
2. Bu klasördeki tüm dosyaları o depoya yükle (GitHub'ın web arayüzünden
   "uploading an existing file" ile sürükle-bırak yapabilirsin, kod
   bilmene gerek yok).
3. **ÇOK ÖNEMLİ**: `.env` dosyasını (varsa) ASLA yükleme — sadece
   `.env.example` yüklenmeli. `.env` içinde gerçek şifreler/token'lar
   olacak, GitHub'da herkese açık olmamalı (depo private olsa bile alışkanlık
   edinmen iyi olur).

## Adım 5 — Render.com'da Dağıt (Background Worker, ücretsiz)

1. https://render.com adresinde ücretsiz hesap aç (GitHub ile giriş
   yapabilirsin, en hızlısı budur).
2. Dashboard'da **New +** → **Background Worker** seç.
3. GitHub deponu (`ceodesk-test-ajani`) bağla, seç.
4. Render, depodaki `render.yaml` dosyasını otomatik tanıyıp ayarları
   önerecek — "Apply" / "Create" ile onayla.
5. **Environment** sekmesine git, aşağıdaki değerleri tek tek ekle (Adım
   1-3'te topladığın gerçek değerlerle):
   - `TEST_COMPANY_NAME`
   - `TEST_COMPANY_PASSWORD`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `VERCEL_API_TOKEN` (isteğe bağlı)
6. **Manual Deploy** → **Deploy latest commit** ile ilk dağıtımı başlat.
7. **Logs** sekmesinden derleme/başlangıç loglarını izleyebilirsin.

**Ücretsiz katman notu**: Render'ın ücretsiz Background Worker'ları normal
web servisleri gibi "uyumaz" (web servisleri trafik olmayınca uyur, ama
worker'lar sürekli çalışır) — ancak Render zaman zaman ücretsiz kaynak
kullanım politikalarını güncelleyebiliyor, ileride bir kısıtlamayla
karşılaşırsan küçük bir ücretli plana geçmen gerekebilir.

## Adım 6 — Doğrula

Dağıtım tamamlanınca Telegram'dan şu mesajı almalısın:

> 🟢 **CEODESK Test Ajanı başlatıldı.**
> Arka planda çalışıyor, siteyi periyodik olarak test edecek.

Gelmezse **Render → Logs** ekranına bak, hata mesajı orada görünecektir
(çoğunlukla eksik/yanlış bir ortam değişkenidir).

---

## Sık Sorulan Sorular

**"Ajan bir hata bulursa ne olur?"**
Telegram'a hatanın ne olduğunu, hangi test adımında bulunduğunu ve varsa
bir ekran görüntüsünü gönderir. Kodu KENDİSİ değiştirmez.

**"Ayarları sonradan değiştirebilir miyim?"**
Evet — Render → Environment sekmesinden değer güncelleyip "Save Changes"
dersin, otomatik yeniden başlar.

**"Test sıklığını değiştirmek istiyorum."**
`TEST_INTERVAL_MINUTES` ortam değişkenini değiştir (dakika cinsinden).

**"Botları/testi geçici olarak durdurmak istiyorum."**
Render → Settings → **Suspend Service**. Tekrar başlatmak için **Resume**.

**"Sonraki aşama (otomatik düzeltme/self-healing) ne zaman?"**
İstediğinde söyle — GitHub PR + Vercel önizleme linki + Telegram bildirimi
üretecek ama canlıya almayı SENİN GitHub'da "Merge" tıklamana bırakacak
şekilde, konuştuğumuz güvenli tasarımla ekleyebilirim.

# CEO'nun Masası — Sosyal Medya İçerik Ajanı

Günde 3 kez (10:00 / 15:00 / 20:00 TR saati) otomatik çalışır, bir tanıtım
görseli + hazır paylaşım metni üretip **Telegram'a gönderir**. Hiçbir sosyal
medya hesabına doğrudan paylaşım YAPMAZ — sen Telegram'dan alıp istediğin
platforma (Instagram, TikTok, X, Facebook…) kendin yapıştırırsın.

## Nasıl çalışıyor

1. **Görsel** — her 3 paylaşımdan **1'i gerçek** (oyunun kendi ekran
   görüntüleri / kullanıcının onayladığı tanıtım görseli, `assets/screenshots/`
   klasöründe, hiçbir ağ isteği gerektirmez, %100 güvenilir), **2'si AI
   üretimi** ([Pollinations.ai](https://pollinations.ai) — ücretsiz, API
   anahtarı gerektirmeyen bir görsel servisi, 18 markaya-uygun prompt
   arasında dönüşümlü).
   - v1'de tüm görseller AI-üretimiydi; canlı testte bazı prompt'ların
     (özellikle soyut/makro kavramlar) markayla alakasız, tuhaf sonuçlar
     verdiği görüldü — hem bu prompt'lar daha güvenli/somut olacak
     şekilde yeniden yazıldı, hem de gerçek görseller eklenerek risk
     azaltıldı.
2. Metin: 12 farklı hazır caption şablonu arasında dönüşümlü seçim —
   **her birinde `ceodesk.net` mutlaka var**.
3. Rotasyon: günün hangi gün olduğu + hangi saat diliminde çalıştığı
   birlikte bir "index" oluşturuyor, böylece aynı gün içindeki 3 paylaşım
   birbirinin aynısı olmuyor, günler ilerledikçe de havuz baştan dönüyor.

## Kurulum

**1. Bu dosya/klasörleri mevcut `ceodesk-test-ajani` deponuza ekleyin:**
- `social_agent.py` → deponun kök dizinine (üzerine yazın, zaten varsa)
- `.github/workflows/social-agent.yml` → mevcut `.github/workflows/` klasörüne
- `assets/` klasörünün TAMAMI (içindeki `screenshots/` alt klasörüyle
  birlikte) → deponun kök dizinine — "Add file → Upload files" ekranına
  `assets` klasörünü doğrudan sürükleyin, GitHub alt klasör yapısını
  korur.

**2. Secrets kontrolü**: Bu depoda muhtemelen zaten `TELEGRAM_BOT_TOKEN` ve
`TELEGRAM_CHAT_ID` secret'ları tanımlı (mevcut Telegram bildirim botu için
kullanılıyor). Eğer öyleyse **hiçbir ek ayar gerekmez** — aynı secret'lar bu
yeni workflow tarafından da otomatik kullanılır.

Eğer bu secret'lar tanımlı değilse: Repo → Settings → Secrets and variables →
Actions → "New repository secret" ile ekleyin.

**3. Test edin**: GitHub'da repo → Actions sekmesi → "Sosyal Medya İçerik
Ajanı" workflow'u → sağ üstten "Run workflow" ile elle bir kez tetikleyip,
Telegram'a gerçekten bir görsel + metin düşüp düşmediğini kontrol edin.

## Dürüstlük notu

Bu script'in Pollinations.ai'ye gerçekten erişip erişemeyeceği, geliştirme
ortamının ağ kısıtları nedeniyle buradan uçtan uca test edilemedi. GitHub
Actions'ın tam internet erişimi olduğu için sorunsuz çalışması beklenir,
ama **ilk çalıştırmayı mutlaka elle tetikleyip (adım 3) doğrulayın.**
Bir sorun çıkarsa (görsel gelmez, hata mesajı), Actions sekmesindeki log'u
bana gönder, birlikte düzeltelim.

## İçerik havuzunu genişletmek

`social_agent.py` içindeki `IMAGE_PROMPTS` ve `CAPTION_TEMPLATES` listeleri
büyüdükçe çeşitlilik artar (tekrar etme süresi uzar). İstediğin zaman yeni
prompt/caption ekleyip commit atman yeterli — kod tarafında başka bir
değişiklik gerekmez.

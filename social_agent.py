#!/usr/bin/env python3
"""
CEO'nun Masası — Sosyal Medya İçerik Ajanı
============================================
Günde 3 kez (GitHub Actions cron ile) çalışır:
  1) Dönen bir havuzdan bir görsel prompt'u seçer (AI görsel üretimi ağırlıklı)
  2) Pollinations.ai'nin ÜCRETSİZ, anahtarsız görsel API'siyle görseli üretir
     (https://image.pollinations.ai/prompt/... — API anahtarı gerekmez)
  3) Dönen bir havuzdan bir caption (paylaşım metni) seçer — ceodesk.net
     adresi HER caption'da mutlaka bulunur
  4) Görsel + caption'ı Telegram bot'a gönderir — kullanıcı buradan alıp
     istediği sosyal medya hesabına kendisi paylaşır (bu script DOĞRUDAN
     hiçbir sosyal medya hesabına paylaşım YAPMAZ, sadece hazırlar).

Gerekli ortam değişkenleri (GitHub Actions secrets):
  TELEGRAM_BOT_TOKEN  — mevcut ceodesk_test_bot token'ı (zaten var olan)
  TELEGRAM_CHAT_ID    — mesajın gideceği sohbet id'si (zaten var olan)

DÜRÜSTLÜK NOTU: Bu script'in Pollinations.ai'ye GERÇEKTEN erişip
erişemeyeceği, geliştirme ortamının (sandbox) ağ kısıtları nedeniyle
buradan test edilemedi — GitHub Actions'ın tam internet erişimi olduğu
için orada çalışması beklenir, ama İLK birkaç çalıştırmayı Telegram'dan
gelen sonuçlarla doğrulaman önerilir.
"""

import os
import sys
import random
import datetime
import urllib.parse
import urllib.request
import json

SITE_URL = "https://ceodesk.net"
POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt"

# v3 (kullanıcı talebi — "oyunumuzdaki [gerçek] görüntülerden neden
# paylaşmıyorsun?"): AI görseli tek başına denetimsiz/öngörülemez olduğu
# kanıtlandı (bkz. v2 notu). Bu liste, oyunun GERÇEK ekran görüntülerini
# (ve kullanıcının kendi onayladığı tanıtım görselini) içeriyor — bunlar
# hiçbir ağ isteği gerektirmez (repo içinde hazır dururlar), bu yüzden
# %100 güvenilirdir ve her zaman markaya birebir uygundur.
REAL_ASSET_IMAGES = [
    "assets/screenshots/factory-hero.jpg",
    "assets/screenshots/kurulus-ekrani.jpg",
    "assets/screenshots/tedarik-zinciri.jpg",
]

# ---------------------------------------------------------------------------
# GÖRSEL PROMPT HAVUZU (İngilizce — Flux modeli İngilizce prompt'larla çok
# daha iyi sonuç veriyor). Kullanıcı talebi: "reklam hissi" ağırlıklı, yani
# hepsi tanıtım/reklam sahnesi gibi kurgulandı. Prompt'larda BİLEREK metin/
# logo/yazı İSTENMEDİ — AI görsel modelleri metni okunaklı render etmekte
# çok kötü; asıl mesaj (marka adı, CTA) Telegram'a giden CAPTION'da veriliyor.
# ---------------------------------------------------------------------------

# v2 (kullanıcı talebi — hata düzeltmesi, GERÇEK CANLI ÇIKTIDA GÖRÜLDÜ):
# İlk listedeki "makro/soyut kavram" tarzı prompt'lar (ör. "birbirine geçen
# dişliler") görsel modelinde markayla hiç alakası olmayan, soyut bir
# desene/mandalaya dönüştü — kanıtlandı, Telegram'a gelen gerçek görsel
# buydu. Bu YENİ liste, HEPSİ net bir OYUNCAK-TARZI İŞ İNSANI FİGÜRÜ veya
# kolayca tanınan somut bir nesne (taç, kasa, gemi, harita) içerecek
# şekilde yeniden yazıldı — modelin soyut/sanatsal yoruma kaçma riskini
# azaltmak için her prompt'un sonuna "clear readable composition, not
# abstract art" vurgusu da eklendi. Yine de: ücretsiz, denetimsiz bir AI
# servisi olduğu için %100 garanti YOK — Telegram'a düşen her görseli
# paylaşmadan önce mutlaka gözle kontrol et.
IMAGE_PROMPTS = [
    "cinematic 3D render, toy-like miniature businessman figure in a hard hat and orange safety vest standing confidently in a golden-lit factory, warm gold and dark navy color palette, dramatic rim lighting, premium advertisement style, ultra detailed, clear readable composition, not abstract art",
    "epic wide shot of a miniature toy factory full of tiny worker figures in yellow hard hats operating a giant polished machine, golden hour lighting, dark moody background, luxury brand advertisement aesthetic, highly detailed 3D render, clear readable composition, not abstract art",
    "close-up cinematic shot of a golden trophy shaped like a crown sitting on a CEO's dark wooden desk, soft golden bokeh lights in background, premium business advertisement photography style, ultra sharp, 8k, clear readable composition, not abstract art",
    "3D render of a tiny toy-like businessman figure standing in front of a glowing world map hologram with golden trade routes connecting glowing cities, dark background, futuristic business technology aesthetic, cinematic lighting, clear readable composition, not abstract art",
    "miniature toy businessman figure climbing a golden staircase made of stacked coins, dark dramatic background, motivational advertisement style, cinematic rim light, ultra detailed 3D render, clear readable composition, not abstract art",
    "a small toy-like factory worker figure pointing at a glowing holographic chart showing rising golden bars, dark navy background, premium tech advertisement look, cinematic depth of field, clear readable composition, not abstract art",
    "toy-like 3D figure of a confident businessman in a suit standing on top of a stack of golden shipping containers at sunset, cinematic wide shot, premium advertisement aesthetic, clear readable composition, not abstract art",
    "close up of a golden crown resting on a stack of blueprint papers on a dark wooden desk, dramatic side lighting, luxury business advertisement photography, ultra sharp detail, clear readable composition, not abstract art",
    "wide cinematic shot of a futuristic factory production line glowing with warm golden light, tiny toy-like worker figures assembling products, dark atmospheric background, premium advertisement render, clear readable composition, not abstract art",
    "3D toy figure of a businessman shaking hands with another toy-like businessman figure in front of a glowing golden holographic globe, dark background with golden particle effects, premium corporate advertisement style, cinematic lighting, clear readable composition, not abstract art",
    "toy-like 3D figures of workers loading golden shipping crates onto a cargo ship at a moody dark harbor at night, warm amber dock lights, cinematic wide advertisement shot, ultra detailed, clear readable composition, not abstract art",
    "miniature toy CEO figure standing at the top of a golden mountain made of stacked gold bars, dark dramatic sky, cinematic wide shot, motivational advertisement aesthetic, ultra detailed 3D render, clear readable composition, not abstract art",
    "wide cinematic shot of tiny toy-like businessman figures working together at glowing control panels inside a dark futuristic command center, golden accent lighting, premium advertisement render, ultra detailed, clear readable composition, not abstract art",
    "3D toy figure of a businessman planting a small golden flag on top of a stack of golden coins shaped like a mountain, dark background, cinematic rim lighting, advertisement quality render, clear readable composition, not abstract art",
    "toy-like 3D businessman figure standing confidently in front of a large golden skyscraper building, dark navy sky, warm rim lighting, premium corporate advertisement style, ultra detailed 3D render, clear readable composition, not abstract art",
    "miniature toy businessman figure holding a golden briefcase, standing on a stack of golden coins, dark dramatic background, cinematic advertisement lighting, ultra detailed 3D render, clear readable composition, not abstract art",
    "toy-like 3D figure of a businessman looking through a large golden telescope pointed at a glowing city skyline at night, dark background, premium advertisement aesthetic, ultra detailed render, clear readable composition, not abstract art",
    "wide shot of a toy-like businessman figure standing proudly next to a large golden rocket ready for launch, dark dramatic sky with warm rim lighting, premium advertisement style, ultra detailed 3D render, clear readable composition, not abstract art",
]

# ---------------------------------------------------------------------------
# CAPTION (paylaşım metni) HAVUZU — Türkçe, ceodesk.net HER ZAMAN dahil.
# {url} yerine SITE_URL otomatik yerleştirilir.
# ---------------------------------------------------------------------------
CAPTION_TEMPLATES = [
    "🏭 Kendi imparatorluğunu kurmaya hazır mısın? CEO'nun Masası'nda şirketini yönet, üretim hattını büyüt, dünyaya açıl!\n\n👉 Ücretsiz oyna: {url}\n\n#stratejioyunu #ücretsizoyun #CEOnunMasası #tarayıcıoyunu",
    "💰 Kasan, çalışanların, itibarın — hepsi senin kararlarına bağlı. Gerçek bir CEO gibi düşünmeye hazır mısın?\n\n🎮 Hemen, kayıt olmadan oyna: {url}\n\n#işsimülasyonu #stratejioyunu #bedavaoyun",
    "🌍 Küçük bir atölyeden küresel bir imparatorluğa... Hikaye senin ellerinde.\n\n▶️ CEO'nun Masası'nı şimdi keşfet: {url}\n\n#CEOnunMasası #stratejioyunu #tarayıcıdaoyna",
    "⚙️ Üretim hattını kur, siparişleri yönet, rakiplerini geride bırak. Tarayıcında, kayıt olmadan, hemen şimdi.\n\n👉 {url}\n\n#ücretsizstratejioyunu #işoyunu #CEOnunMasası",
    "👑 Masanın başına geç, kararları sen ver. CEO'nun Masası'nda şirketin senin vizyonunla büyüyor.\n\n🎮 Ücretsiz oyna: {url}\n\n#stratejioyunu #bedavaoyun #tarayıcıoyunu",
    "📈 İtibarın yükseldikçe kapılar açılıyor — büyük ihaleler, güçlü ortaklıklar, küresel ticaret.\n\nHemen dene: {url}\n\n#CEOnunMasası #işsimülasyonu #stratejioyunu",
    "🤝 Güçlü kooperatifler kur, diğer CEO'larla iş birliği yap, birlikte büyüyün.\n\n👉 Tarayıcında hemen oyna: {url}\n\n#stratejioyunu #kooperatif #CEOnunMasası #bedavaoyun",
    "🏆 Her gün yeni bir sipariş, yeni bir fırsat, yeni bir zorluk. CEO'nun Masası'nda bir gün bile birbirine benzemiyor.\n\n▶️ {url}\n\n#tarayıcıoyunu #stratejioyunu #ücretsizoyun",
    "🚢 Hammadde tedarik et, üretimi büyüt, ürünlerini dünyaya gönder. Küresel ticaret senin bir tık uzağında.\n\n👉 {url}\n\n#CEOnunMasası #stratejioyunu #işsimülasyonu",
    "🔑 Başarının anahtarı doğru kararlar. CEO'nun Masası'nda her seçim, imparatorluğunu şekillendiriyor.\n\n🎮 Kayıt olmadan hemen oyna: {url}\n\n#bedavaoyun #stratejioyunu #tarayıcıoyunu",
    "⛏️ Küçük bir başlangıç, büyük bir vizyon. Zirveye giden yol CEO'nun Masası'nda başlıyor.\n\n👉 {url}\n\n#CEOnunMasası #stratejioyunu #ücretsizoyun",
    "🖥️ İndirme yok, kayıt zorunluluğu yok — sadece aç ve oyna. CEO'nun Masası tarayıcında seni bekliyor.\n\n▶️ {url}\n\n#tarayıcıdaoyna #stratejioyunu #bedavaoyun",
]


# ---------------------------------------------------------------------------
# Zamana dayalı, deterministik rotasyon indeksi — aynı gün içindeki 3 farklı
# çalıştırma (10:00/15:00/20:00 TR) farklı içerik üretsin, gün değiştikçe de
# havuz döngüsel olarak ilerlesin.
# ---------------------------------------------------------------------------
def rotation_index():
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    day_of_year = now_utc.timetuple().tm_yday
    # TR saati UTC+3 (DST yok, 2016'dan beri sabit) — hangi slot olduğunu
    # UTC saatinden çıkarıyoruz: 07:00 UTC->10:00 TR, 12:00 UTC->15:00 TR,
    # 17:00 UTC->20:00 TR. Tam eşleşmezse (manuel tetikleme vs.) en yakın
    # slotu seçer.
    hour = now_utc.hour
    if hour < 10:
        slot = 0
    elif hour < 15:
        slot = 1
    else:
        slot = 2
    return day_of_year * 3 + slot


def pick_image_prompt(index):
    return IMAGE_PROMPTS[index % len(IMAGE_PROMPTS)]


def pick_caption(index):
    # Caption havuzu farklı uzunlukta olabileceği için AYRI bir asal-benzeri
    # adımla ilerletiyoruz ki görsel ile caption hep AYNI index'te
    # eşleşmesin (daha fazla kombinasyon çeşitliliği).
    template = CAPTION_TEMPLATES[(index * 5 + 2) % len(CAPTION_TEMPLATES)]
    return template.format(url=SITE_URL)


def generate_image(prompt, out_path, width=1024, height=1024, seed=None):
    """Pollinations.ai'nin ücretsiz, anahtarsız görsel API'sinden görsel indirir."""
    encoded = urllib.parse.quote(prompt)
    params = {"width": width, "height": height, "nologo": "true"}
    if seed is not None:
        params["seed"] = seed
    query = urllib.parse.urlencode(params)
    url = f"{POLLINATIONS_IMAGE_BASE}/{encoded}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "ceodesk-social-agent/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


def send_telegram_photo(bot_token, chat_id, photo_path, caption):
    """Telegram Bot API ile fotoğraf + caption gönderir (multipart/form-data)."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    boundary = "----ceodeskSocialAgentBoundary"
    with open(photo_path, "rb") as f:
        photo_data = f.read()

    def field(name, value):
        return (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n"
        ).encode("utf-8")

    body = b""
    body += field("chat_id", chat_id)
    body += field("caption", caption)
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"post.jpg\"\r\n"
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    body += photo_data
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("HATA: TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam değişkenleri gerekli.", file=sys.stderr)
        sys.exit(1)

    idx = rotation_index()
    caption = pick_caption(idx)
    out_path = "/tmp/social_post.jpg"

    # v3 (kullanıcı talebi): her 3 paylaşımdan 1'i GERÇEK bir oyun/marka
    # görseli (ağ isteği gerektirmez, %100 güvenilir), diğer 2'si AI
    # üretimi (Pollinations, çeşitlilik için). Bu oran, güvenilirlik ile
    # çeşitliliği dengelemek için seçildi — kolayca değiştirilebilir.
    use_real_asset = (idx % 3 == 0)

    if use_real_asset:
        asset_rel_path = REAL_ASSET_IMAGES[(idx // 3) % len(REAL_ASSET_IMAGES)]
        # Script'in çalıştığı dizine göre (GitHub Actions checkout sonrası
        # repo kökü) göreli yol kullanılıyor.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        asset_full_path = os.path.join(script_dir, asset_rel_path)
        print(f"[social-agent] GERÇEK varlık kullanılıyor: {asset_rel_path}")
        try:
            with open(asset_full_path, "rb") as f:
                data = f.read()
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"[social-agent] gerçek görsel kopyalandı: {out_path}")
        except Exception as e:
            print(f"HATA: gerçek görsel okunamadı: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        prompt = pick_image_prompt(idx)
        seed = idx  # aynı slot'ta tekrar çalışırsa aynı görseli üretir (kararlılık)
        print(f"[social-agent] rotation_index={idx}")
        print(f"[social-agent] AI görsel prompt: {prompt}")
        try:
            generate_image(prompt, out_path, seed=seed)
            print(f"[social-agent] görsel üretildi: {out_path}")
        except Exception as e:
            print(f"HATA: görsel üretilemedi: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"[social-agent] caption:\n{caption}")

    try:
        result = send_telegram_photo(bot_token, chat_id, out_path, caption)
        if not result.get("ok"):
            print(f"HATA: Telegram gönderimi başarısız: {result}", file=sys.stderr)
            sys.exit(1)
        print("[social-agent] Telegram'a başarıyla gönderildi.")
    except Exception as e:
        print(f"HATA: Telegram gönderimi sırasında istisna: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Telegram Bot API üzerinden mesaj ve ekran görüntüsü gönderir.
Twilio/WhatsApp'ın aksine tamamen ücretsizdir ve onay süreci gerektirmez —
KURULUM_REHBERI.md içinde bot oluşturma adımları var.
"""
import logging
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("telegram")
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(text: str) -> bool:
    """Düz metin bildirimi gönderir. Telegram mesaj uzunluğu sınırı (4096
    karakter) aşılırsa mesaj otomatik parçalara bölünür."""
    chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)] or [text]
    ok = True
    for chunk in chunks:
        try:
            resp = requests.post(
                f"{API_BASE}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            if not resp.ok:
                logger.error("Telegram sendMessage başarısız: %s", resp.text)
                ok = False
        except requests.RequestException as exc:
            logger.error("Telegram sendMessage hatası: %s", exc)
            ok = False
    return ok


def send_photo(photo_bytes: bytes, caption: str = "") -> bool:
    """Ekran görüntüsünü doğrudan bellekten (dosyaya yazmadan) gönderir —
    ücretsiz bulut sunucularda disk kalıcı olmayabileceği için ekran
    görüntüsünü diske güvenip sonra okumak yerine anında Telegram'a
    yüklüyoruz."""
    try:
        resp = requests.post(
            f"{API_BASE}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
            files={"photo": ("hata.png", photo_bytes, "image/png")},
            timeout=30,
        )
        if not resp.ok:
            logger.error("Telegram sendPhoto başarısız: %s", resp.text)
            return False
        return True
    except requests.RequestException as exc:
        logger.error("Telegram sendPhoto hatası: %s", exc)
        return False


def send_startup_message():
    send_message(
        "🟢 <b>CEODESK Test Ajanı başlatıldı.</b>\n"
        "Arka planda çalışıyor, siteyi periyodik olarak test edecek."
    )

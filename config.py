"""
Tüm ayarlar burada, tek yerden okunur. Gerçek değerler .env dosyasından
gelir (bkz. .env.example) — kod içinde HİÇBİR gerçek anahtar/şifre yazılı
değildir.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Eksik ortam değişkeni: {name}. .env dosyanıza (veya Render'ın "
            f"Environment sekmesine) bu değeri eklemelisiniz. Detay için "
            f"KURULUM_REHBERI.md dosyasına bakın."
        )
    return value


# --- Test edilecek site -----------------------------------------------------
SITE_URL = _get("SITE_URL", "https://ceonun-masasi.vercel.app")

# Ajanın oyunu test etmek için giriş yapacağı, YALNIZCA TEST amaçlı ayrı bir
# şirket hesabı. Gerçek/kişisel bir hesap KULLANMAYIN — ajan bu hesapla
# tekrar tekrar hammadde satın alacak, sipariş onaylayacak vb.
TEST_COMPANY_NAME = _get("TEST_COMPANY_NAME", "AjanTestSirketi")
TEST_COMPANY_PASSWORD = _get("TEST_COMPANY_PASSWORD", required=True)

# Admin/OP sayfa testleri isteğe bağlıdır (boş bırakılırsa o testler atlanır).
ADMIN_PANEL_SECRET = _get("ADMIN_PANEL_SECRET", "")

# --- Telegram bildirimleri --------------------------------------------------
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID", required=True)

# --- Vercel izleme (isteğe bağlı — boşsa bu adım atlanır) ------------------
VERCEL_API_TOKEN = _get("VERCEL_API_TOKEN", "")
VERCEL_TEAM_ID = _get("VERCEL_TEAM_ID", "")
VERCEL_PROJECT_ID = _get("VERCEL_PROJECT_ID", "")

# --- Zamanlama ---------------------------------------------------------------
# Testler arasında kaç dakika beklenecek. Ücretsiz katmanları yormamak ve
# botların/gerçek oyuncuların trafiğine karışmamak için makul bir aralık.
TEST_INTERVAL_MINUTES = int(_get("TEST_INTERVAL_MINUTES", "20"))

# Aynı hata için art arda kaç bildirim gönderilsin (spam'i önlemek için).
# Sorun devam ettiği sürece her N kontrolde bir hatırlatma gönderilir.
REPEAT_ALERT_EVERY_N_CHECKS = int(_get("REPEAT_ALERT_EVERY_N_CHECKS", "6"))

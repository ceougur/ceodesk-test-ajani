"""
Tüm ayarlar burada, tek yerden okunur. Gerçek değerler GitHub Actions
Secrets'tan (ya da yerel test için .env dosyasından, bkz. .env.example)
gelir — kod içinde HİÇBİR gerçek anahtar/şifre yazılı değildir.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Eksik ortam değişkeni: {name}. GitHub deposu Settings > "
            f"Secrets and variables > Actions bölümüne (ya da yerel test "
            f"için .env dosyanıza) bu değeri eklemelisiniz. Detay için "
            f"KURULUM_REHBERI.md dosyasına bakın."
        )
    return value


# --- Test edilecek site -----------------------------------------------------
SITE_URL = _get("SITE_URL", "https://ceonun-masasi.vercel.app")

# Ajanın oyunu test etmek için giriş yapacağı, YALNIZCA TEST amaçlı ayrı bir
# şirket hesabı. Gerçek/kişisel bir hesap KULLANMAYIN — ajan bu hesapla
# tekrar tekrar hammadde satın alacak, sipariş onaylayacak vb. İkisi de
# 5-10 karakter olmalı (oyunun kendi kuralı).
TEST_COMPANY_NAME = _get("TEST_COMPANY_NAME", required=True)
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

# --- Spam önleme --------------------------------------------------------
# NOT: Test sıklığı artık burada değil — GitHub Actions'ın kendi zamanlayıcısı
# (.github/workflows/test-agent.yml içindeki "cron") kontrol ediyor.
# Aynı hata için art arda kaç bildirim gönderilsin (spam'i önlemek için).
# Sorun devam ettiği sürece her N çalıştırmada bir hatırlatma gönderilir.
REPEAT_ALERT_EVERY_N_CHECKS = int(_get("REPEAT_ALERT_EVERY_N_CHECKS", "6"))

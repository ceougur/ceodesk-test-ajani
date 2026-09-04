"""
CEODESK Test + İzleme Ajanı — ana giriş noktası.

Bu dosya Render'da "Background Worker" olarak çalıştırılmak üzere
tasarlandı: sonsuz bir döngüde belirli aralıklarla (config.py'daki
TEST_INTERVAL_MINUTES) siteyi test eder, Vercel deployment durumunu
kontrol eder ve sorun bulursa Telegram'a bildirim gönderir.

FAZ 1 — bu sürüm SADECE test eder ve bildirir; koda dokunmaz, otomatik
merge/deploy YAPMAZ. "Self-healing" (otomatik yama + PR) katmanı — sizinle
konuşulan güvenlik nedeniyle — ayrı, sonraki bir aşamada ve daima GERÇEK
bir GitHub PR incelemesi gerektirecek şekilde eklenecek.
"""
import asyncio
import logging
import sys
from datetime import datetime, timezone

from config import TEST_INTERVAL_MINUTES, REPEAT_ALERT_EVERY_N_CHECKS
from game_tester import run_full_test_suite
from vercel_monitor import get_latest_deployment_status, is_configured as vercel_configured
from telegram_notify import send_message, send_photo, send_startup_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("main")

# Ardışık kaç kontrolde bu sorunun zaten bildirildiğini tutar — aynı hata
# için her turda yeniden mesaj atıp spam yapmamak içindir.
_ongoing_problem_streak = 0
_last_vercel_state = None


def _now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")


async def run_once():
    global _ongoing_problem_streak, _last_vercel_state

    logger.info("Test turu başlıyor…")
    result = await run_full_test_suite()

    if result.all_ok:
        if _ongoing_problem_streak > 0:
            send_message(f"✅ <b>Sorun düzeldi.</b> Tüm testler geçti. ({_now_str()})")
        _ongoing_problem_streak = 0
        logger.info("Tüm testler başarılı.")
    else:
        _ongoing_problem_streak += 1
        should_notify = (
            _ongoing_problem_streak == 1
            or _ongoing_problem_streak % REPEAT_ALERT_EVERY_N_CHECKS == 0
        )
        logger.warning("%d test başarısız.", len(result.failed_steps))
        if should_notify:
            lines = [f"🔴 <b>CEODESK Test Ajanı — Hata Tespit Edildi</b> ({_now_str()})", ""]
            for step in result.failed_steps:
                lines.append(f"<b>Adım:</b> {step.name}")
                lines.append(f"<b>Sebep:</b> {step.detail}")
                lines.append("")
            lines.append(f"Bu sorun art arda {_ongoing_problem_streak}. kontrolde de görüldü.")
            send_message("\n".join(lines))
            # İlk hata bulunan adımın ekran görüntüsünü de gönder.
            for step in result.failed_steps:
                if step.screenshot:
                    send_photo(step.screenshot, caption=f"Hata anı: {step.name}")
                    break

    if vercel_configured():
        status = get_latest_deployment_status()
        if status and status["state"] != _last_vercel_state:
            if status["state"] in ("ERROR", "CANCELED"):
                send_message(
                    f"🔴 <b>Vercel Deployment Sorunu</b>\n"
                    f"Durum: {status['state']}\n"
                    f"URL: {status['url']}\n"
                    f"({_now_str()})"
                )
            _last_vercel_state = status["state"]


async def main_loop():
    send_startup_message()
    while True:
        try:
            await run_once()
        except Exception as exc:  # noqa: BLE001 - döngü asla tamamen çökmemeli
            logger.exception("Beklenmeyen ajan hatası")
            send_message(f"⚠️ Ajanın kendisinde beklenmeyen bir hata oluştu: {exc}")
        logger.info("Sıradaki tur için %d dakika bekleniyor…", TEST_INTERVAL_MINUTES)
        await asyncio.sleep(TEST_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main_loop())

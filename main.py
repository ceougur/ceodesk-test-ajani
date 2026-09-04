"""
CEODESK Test + İzleme Ajanı — ana giriş noktası.

MİMARİ (GitHub Actions — kullanıcı talebi, Render'ın ücretsiz katmanı
olmadığı ortaya çıkınca buna geçildi): bu dosya SÜREKLİ ÇALIŞAN bir süreç
DEĞİLDİR — GitHub Actions'ın kendi zamanlayıcısı (bkz.
.github/workflows/test-agent.yml, varsayılan her 20 dakikada bir) bu
scripti TEK SEFERLİK çalıştırıp kapatır. Bu yüzden art arda kaç kontrolde
aynı hatanın bildirildiğini (spam önleme) hatırlamak için bir Python
değişkeni YETMEZ — her çalıştırma sıfırdan bir ortamda başlar. Bunun
yerine küçük bir durum dosyası (.agent_state.json) kullanılıyor; bu dosya
GitHub Actions'ın "cache" adımıyla çalıştırmalar arasında korunuyor.

FAZ 1 — bu sürüm SADECE test eder ve bildirir; koda dokunmaz, otomatik
merge/deploy YAPMAZ. "Self-healing" (otomatik yama + PR) katmanı — sizinle
konuşulan güvenlik nedeniyle — ayrı, sonraki bir aşamada ve daima GERÇEK
bir GitHub PR incelemesi gerektirecek şekilde eklenecek.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import REPEAT_ALERT_EVERY_N_CHECKS
from game_tester import run_full_test_suite
from vercel_monitor import get_latest_deployment_status, is_configured as vercel_configured
from telegram_notify import send_message, send_photo, send_startup_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("main")

STATE_FILE = Path(__file__).parent / ".agent_state.json"


def _now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"ongoing_problem_streak": 0, "last_vercel_state": None, "first_run_done": False}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        logger.warning("Durum dosyası okunamadı, sıfırdan başlanıyor.")
        return {"ongoing_problem_streak": 0, "last_vercel_state": None, "first_run_done": False}


def save_state(state: dict):
    try:
        STATE_FILE.write_text(json.dumps(state))
    except OSError:
        logger.exception("Durum dosyası yazılamadı — bir sonraki çalıştırma spam-önleme "
                          "hafızasını kaybedebilir, kritik değil.")


async def run_once():
    state = load_state()

    if not state.get("first_run_done"):
        send_startup_message()
        state["first_run_done"] = True

    logger.info("Test turu başlıyor…")
    result = await run_full_test_suite()

    if result.all_ok:
        if state.get("ongoing_problem_streak", 0) > 0:
            send_message(f"✅ <b>Sorun düzeldi.</b> Tüm testler geçti. ({_now_str()})")
        state["ongoing_problem_streak"] = 0
        logger.info("Tüm testler başarılı.")
    else:
        state["ongoing_problem_streak"] = state.get("ongoing_problem_streak", 0) + 1
        streak = state["ongoing_problem_streak"]
        should_notify = streak == 1 or streak % REPEAT_ALERT_EVERY_N_CHECKS == 0
        logger.warning("%d test başarısız.", len(result.failed_steps))
        if should_notify:
            lines = [f"🔴 <b>CEODESK Test Ajanı — Hata Tespit Edildi</b> ({_now_str()})", ""]
            for step in result.failed_steps:
                lines.append(f"<b>Adım:</b> {step.name}")
                lines.append(f"<b>Sebep:</b> {step.detail}")
                lines.append("")
            lines.append(f"Bu sorun art arda {streak}. kontrolde de görüldü.")
            send_message("\n".join(lines))
            for step in result.failed_steps:
                if step.screenshot:
                    send_photo(step.screenshot, caption=f"Hata anı: {step.name}")
                    break

    if vercel_configured():
        status = get_latest_deployment_status()
        if status and status["state"] != state.get("last_vercel_state"):
            if status["state"] in ("ERROR", "CANCELED"):
                send_message(
                    f"🔴 <b>Vercel Deployment Sorunu</b>\n"
                    f"Durum: {status['state']}\n"
                    f"URL: {status['url']}\n"
                    f"({_now_str()})"
                )
            state["last_vercel_state"] = status["state"]

    save_state(state)


async def main():
    try:
        await run_once()
    except Exception as exc:  # noqa: BLE001 - script asla sessizce çökmemeli
        logger.exception("Beklenmeyen ajan hatası")
        send_message(f"⚠️ Ajanın kendisinde beklenmeyen bir hata oluştu: {exc}")
        raise  # GitHub Actions çalıştırmayı "başarısız" (kırmızı) işaretlesin


if __name__ == "__main__":
    asyncio.run(main())

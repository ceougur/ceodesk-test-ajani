"""
Vercel REST API üzerinden proje deployment durumunu izler.

DÜRÜST NOT: Vercel'in genel/ayrıntılı kullanım-limiti verileri (bant
genişliği, fonksiyon süresi toplamları vb.) için resmi, Hobby (ücretsiz)
planda güvenilir şekilde belgelenmiş basit bir REST endpoint yok — bu
veriler asıl olarak Vercel Dashboard üzerinden izleniyor. Burada GERÇEKTEN
var olan ve doğrulanan `/v6/deployments` uç noktasını kullanıyoruz: en son
deployment'ın durumunu (READY / ERROR / CANCELED / BUILDING) takip eder ve
bir build hatası ya da beklenmedik durum değişikliği olduğunda haber verir.
Ayrıntılı kullanım alarmı istersen Vercel Dashboard > Usage sekmesini
periyodik olarak sen kontrol etmelisin; bu otomasyon onu kapsamaz.
"""
import logging
import requests

from config import VERCEL_API_TOKEN, VERCEL_TEAM_ID, VERCEL_PROJECT_ID

logger = logging.getLogger("vercel_monitor")

API_BASE = "https://api.vercel.com"


def is_configured() -> bool:
    return bool(VERCEL_API_TOKEN and VERCEL_PROJECT_ID)


def get_latest_deployment_status():
    """En son (production) deployment'ın durumunu döndürür, örn.
    {'state': 'READY', 'url': '...', 'created': ...} veya hata olursa None."""
    if not is_configured():
        return None
    params = {"projectId": VERCEL_PROJECT_ID, "limit": 1, "target": "production"}
    if VERCEL_TEAM_ID:
        params["teamId"] = VERCEL_TEAM_ID
    try:
        resp = requests.get(
            f"{API_BASE}/v6/deployments",
            headers={"Authorization": f"Bearer {VERCEL_API_TOKEN}"},
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        deployments = resp.json().get("deployments", [])
        if not deployments:
            return None
        d = deployments[0]
        return {"state": d.get("state"), "url": d.get("url"), "created": d.get("created")}
    except requests.RequestException as exc:
        logger.error("Vercel API hatası: %s", exc)
        return None

"""
CEODESK Redis Yedekleme Scripti.

Tüm ceo-* anahtarlarını (rate-limit sayaçları HARİÇ — bunlar zaten kısa
ömürlü, yedeklemeye değer bir bilgi taşımıyor) tek bir JSON dosyasına
yedekler. Redis'in farklı veri tiplerini (string/hash/set/list/zset) doğru
şekilde okuyup geri yüklenebilir formatta saklar — bu yüzden anahtar
isimlerini tek tek bilmeye gerek yok, ileride eklenen yeni özellikler
otomatik olarak dahil olur.

Kullanım: python backup.py  (REDIS_URL ortam değişkeni gerekli)
Çıktı: redis-backup-<tarih>.json (aynı dizine yazılır)
"""
import json
import os
import sys
from datetime import datetime, timezone

import redis

EXCLUDE_PREFIXES = ("ceo-ratelimit:",)


def dump_key(client, key):
    key_type = client.type(key)
    ttl = client.ttl(key)  # -1: süresiz, -2: yok (yarış durumu, atlanır)
    if key_type == "string":
        payload = {"type": "string", "value": client.get(key)}
    elif key_type == "hash":
        payload = {"type": "hash", "value": client.hgetall(key)}
    elif key_type == "set":
        payload = {"type": "set", "value": list(client.smembers(key))}
    elif key_type == "list":
        payload = {"type": "list", "value": client.lrange(key, 0, -1)}
    elif key_type == "zset":
        payload = {"type": "zset", "value": client.zrange(key, 0, -1, withscores=True)}
    else:
        payload = {"type": "unsupported", "value": None}
    payload["ttl"] = ttl if ttl and ttl > 0 else None
    return payload


def main():
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        print("HATA: REDIS_URL ortam değişkeni tanımlı değil.", file=sys.stderr)
        sys.exit(1)

    client = redis.from_url(redis_url, decode_responses=True)
    client.ping()

    backup = {}
    cursor = 0
    total = 0
    while True:
        cursor, keys = client.scan(cursor=cursor, match="ceo-*", count=500)
        for key in keys:
            if any(key.startswith(p) for p in EXCLUDE_PREFIXES):
                continue
            backup[key] = dump_key(client, key)
            total += 1
        if cursor == 0:
            break

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"redis-backup-{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"createdAt": timestamp, "keyCount": total, "data": backup}, f, ensure_ascii=False)

    print(f"Yedekleme tamamlandı: {filename} ({total} anahtar)")


if __name__ == "__main__":
    main()

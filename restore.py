"""
CEODESK Redis Geri Yükleme Scripti.

backup.py'nin ürettiği bir JSON dosyasını Redis'e geri yükler. YIKICI bir
işlemdir (aynı isimli anahtarların üzerine yazar) — bu yüzden BİLEREK
--confirm bayrağı olmadan çalışmaz.

Kullanım:
  python restore.py redis-backup-2026-09-04_12-00-00.json --confirm

REDIS_URL ortam değişkeni, GERİ YÜKLENECEK (hedef) Redis'i göstermelidir —
production'a yanlışlıkla eski veri yazmamak için bu değeri her çalıştırmadan
önce kontrol edin.
"""
import argparse
import json
import os
import sys

import redis


def restore_key(client, key, payload):
    client.delete(key)
    value_type = payload.get("type")
    value = payload.get("value")
    if value_type == "string":
        client.set(key, value)
    elif value_type == "hash":
        if value:
            client.hset(key, mapping=value)
    elif value_type == "set":
        if value:
            client.sadd(key, *value)
    elif value_type == "list":
        if value:
            client.rpush(key, *value)
    elif value_type == "zset":
        if value:
            client.zadd(key, {member: score for member, score in value})
    else:
        return False
    ttl = payload.get("ttl")
    if ttl:
        client.expire(key, ttl)
    return True


def main():
    parser = argparse.ArgumentParser(description="CEODESK Redis yedeğini geri yükler.")
    parser.add_argument("backup_file", help="backup.py tarafından üretilen JSON dosyası")
    parser.add_argument("--confirm", action="store_true", help="Gerçekten geri yüklemeyi onayla (yoksa sadece önizleme yapılır)")
    args = parser.parse_args()

    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        print("HATA: REDIS_URL ortam değişkeni tanımlı değil.", file=sys.stderr)
        sys.exit(1)

    with open(args.backup_file, "r", encoding="utf-8") as f:
        backup = json.load(f)

    data = backup.get("data", {})
    print(f"Yedek dosyası: {args.backup_file}")
    print(f"Oluşturulma zamanı: {backup.get('createdAt')}")
    print(f"Anahtar sayısı: {len(data)}")

    if not args.confirm:
        print("\nÖNİZLEME MODU — hiçbir şey yazılmadı. Gerçekten geri yüklemek için --confirm ekleyin.")
        return

    client = redis.from_url(redis_url, decode_responses=True)
    client.ping()

    restored = 0
    for key, payload in data.items():
        if restore_key(client, key, payload):
            restored += 1
    print(f"\nGeri yükleme tamamlandı: {restored}/{len(data)} anahtar yazıldı.")


if __name__ == "__main__":
    main()

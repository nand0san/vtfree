from __future__ import annotations

import os
import time
from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv

import vtfree.log
from vtfree import VTClient

# ---------- Configuración de entorno ---------------------------------- #
load_dotenv()

API_KEYS = [k.strip() for k in os.getenv("VT_KEYS", "").split(",") if k.strip()]
if not API_KEYS:
    raise SystemExit("❌  No se encontraron claves VT en la variable VT_KEYS")

LOG_PATH = Path("vtfree_verbose.log")
vtfree.log.configure(path=LOG_PATH, level=10)  # 10 = DEBUG

# ---------- Instanciar cliente ---------------------------------------- #
vt = VTClient(API_KEYS, validate=True)

# IOCs de prueba (públicos) -------------------------------------------- #
IOC_HASH = "99017f6eebbac24f351415dd410d522d"  # EICAR
IOC_URL_ID = "aHR0cDovL2V4YW1wbGUuY29t"  # dummy
IOC_DOMAIN = "example.com"
IOC_IP = "1.1.1.1"

# ---------- Lanzar peticiones ----------------------------------------- #
print("\n• file_report")
pprint(vt.file_report(IOC_HASH)["data"]["type"])

print("\n• url_report")
pprint(vt.url_report(IOC_URL_ID)["data"]["type"])

print("\n• domain_report")
pprint(vt.domain_report(IOC_DOMAIN)["data"]["type"])

print("\n• ip_report")
pprint(vt.ip_report(IOC_IP)["data"]["type"])

# 5ª llamada (opcional) para observar rotación de clave si agotamos el token
# print("\n• segunda file_report (trigger key rotation)")
# pprint(vt.file_report(IOC_HASH)["data"]["type"])

# ---------- Snapshot de estado ---------------------------------------- #
print("\n=== KEY STATUS ===")
for entry in vt.key_status():
    pprint(entry)

# ---------- Verificar que el log existe y mostrar últimas líneas ------ #
time.sleep(0.2)
if LOG_PATH.exists():
    print(f"\n=== LOG {LOG_PATH} (tail 20) ===")
    for ln in LOG_PATH.read_text(encoding="utf-8").splitlines()[-20:]:
        print(ln)
else:
    print("⚠️  No se creó el fichero de log")


if __name__ == "__main__":
    # ejecución manual: no asserts
    exit()

# ── pytest validations ──────────────────────────────────────────────── #
snapshot = vt.key_status()
# contamos llamadas registradas (todas deben sumar 4)
total_daily = sum(int(s["daily"].split("/")[0]) for s in snapshot)
assert total_daily == 4, f"esperaba 4 llamadas registradas y tengo {total_daily}"

# al menos una key debe estar en WAIT_MIN o READY con minute>0
assert any(int(s["minute"].split("/")[0]) > 0 for s in snapshot)

assert LOG_PATH.exists(), "log file no creado"

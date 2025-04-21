# vtfree

**Cliente ligero, prudente y tipado para la _VirusTotal Public API v3_.**

---

## Características

| Descripción                                                                                       |
|---------------------------------------------------------------------------------------------------|
| Emplea varias API keys a la vez, rotándolas y revisando que no sobrepasen cuotas.                 | 
| Respeta la cuota pública (4 req/min · 500 req/día) mediante un *token‑bucket* por API‑Key.        |
| Rotación automática de claves y detección de códigos `429` / “User banned”.                       |
| Logging rotativo UTF‑8 (`~/.vtfree/vtfree.log`, 2 MB × 3).                                        |
| Tipado estático (compatible ‑strict con `mypy`).                                                  |
| API orientada a objetos (`VTClient`) más _wrappers_ retro‑compatibles (`check_urls_in_vt`, etc.). |
| Solo depende de `requests` y **opcionalmente** `python‑dotenv`.                                   |

---

## Instalación

```bash
pip install vtfree                  # versión estable desde PyPI

# o, para desarrollo:
pip install -e .[dev]               # dentro del repo clonado
```

---

## Configuración de claves

1. Añade tus claves públicas en un `.env` separadas por comas, sin ponerlas entre comillas:

   ```dotenv
   VT_KEYS=key1,key2,key3,key4
   ```

2. Carga el fichero `.env` al arrancar tu script:

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

---

## Uso básico

```python
import os, vtfree.log
from dotenv import load_dotenv
from vtfree import VTClient

load_dotenv()
vtfree.log.configure()                          # ~/.vtfree/vtfree.log

keys = os.getenv("VT_KEYS", "").split(",")
vt   = VTClient(keys, validate=True)            # smoke‑test opcional

report = vt.file_report("99017f6eebbac24f351415dd410d522d")
print(report["data"]["attributes"]["type"])     # 'file'

print(vt.key_status())                          # snapshot de cuotas
```

---

## Wrappers de compatibilidad (scripts heredados)

```python
from vtfree.contrib import (
    set_default_client, check_urls_in_vt,
    check_ips_in_vt,     check_domains_in_vt,
    check_hashes_in_vt,
)

set_default_client(vt)  # usa la instancia ya creada

res = []
res += check_urls_in_vt([
    "http://homespottersf.com/sm/googledocs1/index.html",
    "https://undec-ab94.djuleircendku.workers.dev/b96043f6-39ae-43f3-aef7-d1371cf249e8",
])
res += check_ips_in_vt(["66.240.205.34"])
res += check_domains_in_vt(["karasserybank.com", "iownyour.biz"])
res += check_hashes_in_vt(["e0c0cbc50a9ed4d01a176497c8dba913cbbba515ea701a67ef00dcb7c8a84368"])

for r in res:
    print(r)
```

Ejemplo de salida:

```
{'ioc_type': 'url',    'score': '3/24',  'ioc': 'http://homespottersf.com/...', ...}
{'ioc_type': 'ip',     'score': '13/35', 'ioc': '66.240.205.34',               ...}
{'ioc_type': 'domain', 'score': '0/22',  'ioc': 'karasserybank.com',           ...}
```

---

## Registro de eventos

```text
2025‑04‑21 19:12:01 INFO  vtfree.client Key 0900…21cf → HTTP 200
2025‑04‑21 19:12:16 DEBUG vtfree.client Key status: [{'key': '0900…21cf', ...}]
```

*Ubicación*: `~/.vtfree/vtfree.log` (UTF‑8, rotación 2 MB × 3).

Para registrar en otra ruta o cambiar el nivel:

```python
vtfree.log.configure(path="vtfree_debug.log", level=10)   # DEBUG
```

---

## Buenas prácticas con la cuota gratuita

| Regla VirusTotal            | Implementación en **vtfree**                                               |
|-----------------------------|-----------------------------------------------------------------------------|
| 4 peticiones / minuto       | Token‑bucket deslizante de 60 s por API‑Key.                                |
| 500 peticiones / día        | Contador diario reiniciado a las 00:00 UTC.                                 |
| `429` → esperar             | Marca la clave como *BANNED*, pasa a la siguiente y hace _back‑off_ de 15 s.|

---

## Licencia

MIT © 2025 *Nand0san* — puedes usar esta librería en proyectos comerciales y
open‑source manteniendo la nota de copyright.

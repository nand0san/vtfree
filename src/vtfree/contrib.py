"""
Wrappers de compatibilidad que exponen las funciones históricas:
`check_urls_in_vt`, `check_ips_in_vt`, `check_domains_in_vt`, `check_hashes_in_vt`.

Cada wrapper acepta una lista de IOCs y devuelve la misma estructura:
    [{'ioc_type': 'url', 'score': '3/24', 'ioc': 'http://…', 'error': None}, …]

Requiere que el usuario cree **una** instancia global de `VTClient`
y la pase por parámetro o la configure vía `set_default_client()`.
"""
from __future__ import annotations
import base64
from typing import Dict, List, Optional

from .client import VTClient

_DEFAULT_CLIENT: Optional[VTClient] = None


def set_default_client(client: VTClient) -> None:
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = client


def _ensure() -> VTClient:
    if _DEFAULT_CLIENT is None:
        raise RuntimeError("No default VTClient set – llama set_default_client() primero")
    return _DEFAULT_CLIENT


def _process_result(resp: dict, ioc: str, ioc_type: str) -> Dict[str, str]:
    """
    Convierte la respuesta JSON de VT en la estructura clásica {ioc_type, score, …}
    """
    result = {'ioc_type': ioc_type, 'score': 'N/A', 'ioc': ioc, 'error': None}
    if resp:
        stats = resp["data"]["attributes"]["last_analysis_stats"]
        result["score"] = f'{stats["malicious"]}/{stats["malicious"] + stats["undetected"]}'
    return result


# --- wrappers públicos ------------------------------------------------- #
def check_urls_in_vt(urls: List[str]) -> List[Dict[str, str]]:
    vt = _ensure()
    out: List[Dict[str, str]] = []
    for url in urls:
        url_id = base64.urlsafe_b64encode(url.encode()).rstrip(b"=").decode()
        out.append(_process_result(vt.url_report(url_id), url, "url"))
    return out


def check_ips_in_vt(ips: List[str]) -> List[Dict[str, str]]:
    vt = _ensure()
    return [_process_result(vt.ip_report(ip), ip, "ip") for ip in ips]


def check_domains_in_vt(domains: List[str]) -> List[Dict[str, str]]:
    vt = _ensure()
    return [_process_result(vt.domain_report(d), d, "domain") for d in domains]


def check_hashes_in_vt(hashes: List[str]) -> List[Dict[str, str]]:
    vt = _ensure()
    return [_process_result(vt.file_report(h), h, "hash") for h in hashes]

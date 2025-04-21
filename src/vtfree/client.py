# vtclient.py
from __future__ import annotations
import itertools
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Deque, Dict, Optional, Sequence
import requests
import logging
from .exceptions import VTClientError
from .utils import random_user_agent, obfuscate


# logger local
_log = logging.getLogger("vtfree.client")

__all__ = ["VTClient"]


@dataclass
class _KeyState:
    key: str
    minute_window: Deque[float] = field(default_factory=deque)  # ts de las últimas llamadas
    daily_count: int = 0
    banned: bool = False
    last_error: Optional[int] = None

    def reset_day(self) -> None:
        self.daily_count = 0


class VTClient:
    """
    Cliente ligero y prudente para la *Public API v3* de VirusTotal.

    :param api_keys: Secuencia de API keys públicas.
    :param validate: Si *True* se realiza un *smoke‑test* de cada key
                     contra un hash conocido inofensivo antes de usarlas.
    :param session:  `requests.Session` externo (inyectable para tests).
    """

    _PUBLIC_ENDPOINT = "https://www.virustotal.com/api/v3"
    _TEST_HASH = "99017f6eebbac24f351415dd410d522d"  # eicar

    # Cuota pública
    _MAX_PER_MIN = 4
    _MAX_PER_DAY = 500

    def __init__(self,
                 api_keys: Sequence[str],
                 *,
                 validate: bool = False,
                 session: Optional[requests.Session] = None) -> None:
        if not api_keys:
            raise ValueError("Se requiere al menos una API key.")
        # Copiar y barajar para repartir carga
        keys = list(dict.fromkeys(api_keys))
        random.shuffle(keys)
        self._states: Dict[str, _KeyState] = {k: _KeyState(k) for k in keys}
        self._key_iter = itertools.cycle(keys)
        self._session = session or requests.Session()

        if validate:
            self._validate_keys()

        self._midnight_utc = self._next_midnight_utc()

    # ---------- API pública alto nivel ---------------------------------- #

    def file_report(self, sha256: str) -> dict:
        return self._get(f"/files/{sha256}")

    def url_report(self, url_id: str) -> dict:
        return self._get(f"/urls/{url_id}")

    def domain_report(self, domain: str) -> dict:
        return self._get(f"/domains/{domain}")

    def ip_report(self, ip: str) -> dict:
        return self._get(f"/ip_addresses/{ip}")

    # ---------- Núcleo de peticiones ------------------------------------ #

    def _get(self, path: str, **params) -> dict:
        url = f"{self._PUBLIC_ENDPOINT}{path}"
        key_state = self._next_available_key()
        headers = {
            "x-apikey": key_state.key,
            "User-Agent": random_user_agent(),
        }
        response = self._session.get(url, headers=headers, params=params or None)
        self._register_call(key_state, response)
        if response.status_code == 200:
            return response.json()
        raise VTClientError(f"Error {response.status_code}: {response.text[:120]}")

    # ---------- Gestión interna de cuotas -------------------------------- #

    def _next_available_key(self) -> _KeyState:
        self._reset_if_new_day()
        for _ in range(len(self._states)):
            state = self._states[next(self._key_iter)]
            if state.banned:
                continue
            self._release_old_minute_tokens(state)
            if (len(state.minute_window) < self._MAX_PER_MIN
                    and state.daily_count < self._MAX_PER_DAY):
                return state
        _log.warning("Sin claves disponibles: back‑off 15 s")
        time.sleep(15)
        raise VTClientError("No hay API keys disponibles en este momento.")

    @staticmethod
    def _register_call(state: _KeyState, resp: requests.Response) -> None:
        now = time.monotonic()
        state.minute_window.append(now)
        state.daily_count += 1
        state.last_error = resp.status_code if resp.status_code != 200 else None

        # if resp.status_code == 429:
        #     state.banned = True  # VT suele banear temporalmente → se desactiva
        # elif b"User is banned" in resp.content:
        #     state.banned = True
        if resp.status_code == 429 or b"User is banned" in resp.content:
            state.banned = True
            _log.error("Key %s baneada (HTTP %s)", obfuscate(state.key), resp.status_code)

    # ---------- Utilidades ----------------------------------------------- #

    @staticmethod
    def _next_midnight_utc() -> float:
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc).timestamp()

    def _reset_if_new_day(self) -> None:
        if time.time() >= self._midnight_utc:
            for st in self._states.values():
                st.reset_day()
                st.banned = False
            self._midnight_utc = self._next_midnight_utc()

    @staticmethod
    def _release_old_minute_tokens(state: _KeyState) -> None:
        limit_ts = time.monotonic() - 60
        while state.minute_window and state.minute_window[0] < limit_ts:
            state.minute_window.popleft()

    # def _validate_keys(self) -> None:
    def _validate_keys(self) -> None:
        for k in list(self._states):
            try:
                self._session.get(
                    f"{self._PUBLIC_ENDPOINT}/files/{self._TEST_HASH}",
                    headers={"x-apikey": k},
                    timeout=10,
                )
            except Exception:
                self._states[k].banned = True
                _log.error("Key %s inválida/bloqueada al iniciar", obfuscate(k))

# ---------- Métricas --------------------------------------------------- #

    def key_status(self) -> list[dict[str, str]]:
        """Snapshot del estado de cada API key ofuscada."""
        self._reset_if_new_day()
        out = []
        for st in self._states.values():
            status = ("BANNED" if st.banned else
                      "WAIT_MIN" if len(st.minute_window) >= self._MAX_PER_MIN else
                      "WAIT_DAY" if st.daily_count >= self._MAX_PER_DAY else
                      "READY")
            out.append({
                "key": obfuscate(st.key),
                "status": status,
                "minute": f"{len(st.minute_window)}/{self._MAX_PER_MIN}",
                "daily": f"{st.daily_count}/{self._MAX_PER_DAY}",
            })
        _log.info("Key status: %s", out)
        return out

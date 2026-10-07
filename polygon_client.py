# ==============================================================================
# CLIENTE COMPARTIDO DE POLYGON.IO
# Solo transporte: control de ritmo por ventana deslizante, timeout, reintentos
# ante 429 / 5xx / fallos de red y paginacion que nunca devuelve resultados a
# medias sin avisar. Cada script conserva su propia configuracion, sus
# endpoints y su forma de procesar los datos.
# ==============================================================================

import os
import random
import threading
import time
import warnings
from collections import deque
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

POLYGON_BASE_URL = "https://api.polygon.io"

# Cupo por defecto del pipeline. El plan gratuito de Polygon ronda las 5
# llamadas por minuto; POLYGON_CALLS_PER_MINUTE lo baja si hace falta. Se lee
# al crear el cliente, no al importar, para que load_dotenv() ya haya corrido.
DEFAULT_CALLS_PER_MINUTE = 100


def calls_per_minute_configurado():
    try:
        return int(os.environ.get("POLYGON_CALLS_PER_MINUTE", DEFAULT_CALLS_PER_MINUTE))
    except ValueError:
        return DEFAULT_CALLS_PER_MINUTE


class PolygonError(RuntimeError):
    """La API no devolvio una respuesta utilizable tras agotar los reintentos."""


class PolygonNotFound(PolygonError):
    """HTTP 404: recurso inexistente (p. ej. activo sin mercado de opciones)."""


class PolygonTruncated(PolygonError):
    """La paginacion alcanzo el tope de paginas y quedaban resultados por pedir."""


NO_OPTION_DATA = "no option data returned"


class NoOptionData(RuntimeError):
    """El ticker no tiene cadena de opciones utilizable en esta corrida."""


def failure_reason(exc, default=NO_OPTION_DATA):
    """Motivo de exclusion para el JSON de senales a partir de una excepcion.

    Un 404 o una cadena vacia significan que no hay datos de opciones; un fallo
    de la API (429 agotado, 5xx, red) o un error de codigo no lo son, y se
    reportan como tales para que no se confundan con un activo sin opciones.
    """
    if exc is None or isinstance(exc, PolygonNotFound):
        return default
    if isinstance(exc, NoOptionData):
        return str(exc).strip() or default
    if isinstance(exc, PolygonError):
        return f"api error: {exc}"
    texto = str(exc).strip()
    return f"error: {type(exc).__name__}" + (f": {texto}" if texto else "")


class _RateLimiter:
    # Ventana deslizante: como mucho `calls` llamadas en cualquier intervalo de
    # `period` segundos. Permite rafagas de hasta `calls` llamadas y solo
    # espera cuando la ventana esta llena, en vez de un espaciado fijo.
    def __init__(self, calls, period=60.0):
        self.calls = max(int(calls), 1)
        self.period = float(period)
        self.stamps = deque()
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            while True:
                now = time.monotonic()
                while self.stamps and now - self.stamps[0] >= self.period:
                    self.stamps.popleft()
                if len(self.stamps) < self.calls:
                    self.stamps.append(now)
                    return
                time.sleep(self.period - (now - self.stamps[0]) + 0.05)


# Un limitador por API key: todos los clientes que comparten key comparten cupo.
_LIMITERS = {}
_LIMITERS_LOCK = threading.Lock()


def _limiter_for(api_key, calls_per_minute):
    with _LIMITERS_LOCK:
        if api_key not in _LIMITERS:
            _LIMITERS[api_key] = _RateLimiter(calls_per_minute)
        return _LIMITERS[api_key]


def retry_after_seconds(response, now=None):
    """Parse a Retry-After header as seconds, or None when it is absent/invalid."""
    if response is None:
        return None
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    raw = headers.get("Retry-After")
    if raw is None or str(raw).strip() == "":
        return None
    text = str(raw).strip()
    try:
        return max(float(text), 0.0)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max((when - now).total_seconds(), 0.0)


def retry_backoff_seconds(attempt, base, response=None, jitter=None, now=None):
    """Wait before retry ``attempt`` (1 = first failure).

    HTTP 429 and 5xx honor Retry-After when the header is present. Otherwise
    the wait is exponential (``base * 2**(attempt-1)``) plus equal jitter in
    ``[0, delay]``.
    """
    status = getattr(response, "status_code", None) if response is not None else None
    if status == 429 or (status is not None and status >= 500):
        honored = retry_after_seconds(response, now=now)
        if honored is not None:
            return honored
    delay = float(base) * (2 ** (max(int(attempt), 1) - 1))
    if jitter is None:
        jitter = random.random()
    return delay + float(jitter) * delay


class PolygonClient:
    def __init__(self, api_key=None, calls_per_minute=None,
                 timeout=20, max_retries=4, retry_wait=15.0,
                 base_url=POLYGON_BASE_URL, verbose=True):
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise PolygonError("No hay POLYGON_API_KEY configurada (archivo .env o entorno).")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        if calls_per_minute is None:
            calls_per_minute = calls_per_minute_configurado()
        self.limiter = _limiter_for(self.api_key, calls_per_minute)
        self.session = requests.Session()

    def _url(self, path_or_url):
        if path_or_url.startswith("http"):
            return path_or_url
        return self.base_url + path_or_url

    def get(self, path_or_url, params=None):
        """Devuelve el JSON de la respuesta o lanza PolygonError. Nunca devuelve None."""
        url = self._url(path_or_url)
        params = dict(params or {})
        params["apiKey"] = self.api_key
        # La key nunca aparece en los mensajes de error
        url_log = url.split("?")[0]

        ultimo_error = None
        for intento in range(1, self.max_retries + 2):
            self.limiter.wait()
            resp = None
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                ultimo_error = f"fallo de red: {exc.__class__.__name__}"
            else:
                status = resp.status_code
                if status == 200:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise PolygonError(f"Respuesta no JSON en {url_log}") from exc
                if status == 404:
                    raise PolygonNotFound(f"Recurso no encontrado (404) en {url_log}")
                if status != 429 and status < 500:
                    raise PolygonError(f"HTTP {status} en {url_log}: {resp.text[:200]}")
                ultimo_error = f"HTTP {status}"

            if intento > self.max_retries:
                break
            espera = retry_backoff_seconds(intento, self.retry_wait, resp)
            if self.verbose:
                print(f"    [polygon] {ultimo_error} en {url_log}; reintento "
                      f"{intento}/{self.max_retries} en {espera:.1f}s...")
            time.sleep(espera)

        raise PolygonError(f"{ultimo_error} en {url_log} tras {self.max_retries} reintentos")

    def paginate(self, path_or_url, params=None, max_pages=50, allow_truncation=False):
        """
        Sigue next_url y devuelve todos los `results`. Si una pagina falla se
        lanza PolygonError (no se devuelve la cadena a medias). Si se alcanza
        max_pages y aun quedan paginas, lanza PolygonTruncated salvo que
        allow_truncation=True, en cuyo caso avisa y devuelve lo acumulado.
        """
        payload = self.get(path_or_url, params)
        resultados = list(payload.get("results") or [])
        paginas = 1
        next_url = payload.get("next_url")
        while next_url:
            if paginas >= max_pages:
                msg = (f"Paginacion de {self._url(path_or_url).split('?')[0]} cortada en "
                       f"{max_pages} paginas ({len(resultados)} resultados) con datos pendientes")
                if allow_truncation:
                    warnings.warn(msg, RuntimeWarning)
                    break
                raise PolygonTruncated(msg)
            payload = self.get(next_url)
            resultados.extend(payload.get("results") or [])
            paginas += 1
            next_url = payload.get("next_url")
        return resultados

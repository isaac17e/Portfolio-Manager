# ==============================================================================
# CLIENTE COMPARTIDO DE POLYGON.IO
# Solo transporte: control de ritmo por ventana deslizante, timeout, reintentos
# ante 429 / 5xx / fallos de red y paginacion que nunca devuelve resultados a
# medias sin avisar. Cada script conserva su propia configuracion, sus
# endpoints y su forma de procesar los datos.
# ==============================================================================

import os
import threading
import time
import warnings
from collections import deque

import requests

POLYGON_BASE_URL = "https://api.polygon.io"

# El plan basico limita ~5 llamadas por minuto por API key, en TODOS los
# endpoints. Al subir de plan basta con fijar POLYGON_CALLS_PER_MINUTE en el
# .env (p. ej. 100); todos los scripts lo toman de ahi. Se lee al crear el
# cliente, no al importar, para que load_dotenv() de cada script ya haya corrido.
DEFAULT_CALLS_PER_MINUTE = 5


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
            espera = self.retry_wait * intento
            if self.verbose:
                print(f"    [polygon] {ultimo_error} en {url_log}; reintento "
                      f"{intento}/{self.max_retries} en {espera:.0f}s...")
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

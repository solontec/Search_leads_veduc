import os
import hashlib
import requests
from typing import Optional

try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    HTTPAdapter = None
    Retry = None


_DEBUG_HTTP = os.getenv("DEBUG_HTTP", "0").strip().lower() in {"1", "true", "yes", "y"}
_FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "20"))
_FETCH_DEBUG_MAX_CHARS = int(os.getenv("FETCH_DEBUG_MAX_CHARS", "2000"))


def _dump_debug_html(url: str, status_code: int, text: str) -> None:
    safe_hash = hashlib.sha256(url.encode("utf-8", errors="ignore")).hexdigest()[:12]
    filename = f"debug_http_{safe_hash}_{status_code}.html"
    try:
        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
        print(f"[DEBUG] HTML dump salvo em: {filename}")
    except Exception as exc:  # pragma: no cover
        print(f"[DEBUG] Falha ao salvar dump do HTML: {exc}")


_SESSION = requests.Session()
if HTTPAdapter is not None and Retry is not None:
    # Regras simples: retry para falhas transitórias e throttling.
    _retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=_retry)
    _SESSION.mount("http://", adapter)
    _SESSION.mount("https://", adapter)


def fetch(url: str) -> Optional[str]:
    """
    Busca HTML para o parser.

    Importante: mesmo quando o `status_code` não é 200, tentamos retornar o
    `response.text` se houver conteúdo, porque páginas de bloqueio/captcha
    ainda podem conter título/H1 e nos ajudam a debugar e salvar progresso.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive",
    }

    try:
        response = _SESSION.get(
            url,
            headers=headers,
            timeout=_FETCH_TIMEOUT,
            allow_redirects=True,
        )

        text = response.text or ""
        if not text.strip():
            print(
                f"[DEBUG] fetch sem conteúdo: status={response.status_code} len={len(text)} url={url}"
            )
            return None

        if response.status_code != 200:
            preview = text[:_FETCH_DEBUG_MAX_CHARS].replace("\n", " ") if text else ""
            print(
                f"[DEBUG] Status diferente de 200: status={response.status_code} len={len(text)} url={url}"
            )
            print(f"[DEBUG] Preview HTML (primeiros chars): {preview[:300]}")

            if _DEBUG_HTTP:
                _dump_debug_html(url, response.status_code, text)

        return text

    except requests.RequestException as exc:
        print(f"[DEBUG] Erro no fetch (requests): {type(exc).__name__}: {exc} url={url}")
        return None
    except Exception as exc:  # pragma: no cover
        print(f"[DEBUG] Erro no fetch (genérico): {type(exc).__name__}: {exc} url={url}")
        return None
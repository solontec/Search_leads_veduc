import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch(url: str, timeout: int = 20) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None
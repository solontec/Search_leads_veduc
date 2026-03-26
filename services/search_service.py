import os
import requests
from dotenv import load_dotenv
import html as html_lib
import re
from typing import Any

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def clean_linkedin_url(url: str) -> str:
    url = url.split("?")[0]
    url = url.replace("/pt", "").replace("/en", "")
    return url.rstrip("/")

def search_profile_urls(query: str) -> list[str]:
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY não encontrado no .env")

    urls = []

    for page in range(1, 4):
        payload = {
            "q": query,
            "gl": "br",
            "hl": "pt-br",
            "page": page
        }

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://google.serper.dev/search",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            print(f"[ERROR] Serper status={response.status_code}")
            print(f"[ERROR] Resposta: {response.text}")
            break

        data = response.json()
        organic = data.get("organic", [])

        print(f"[DEBUG] Query: {query} | page={page} | resultados={len(organic)}")

        if not organic:
            break

        for item in organic:
            link = item.get("link")
            if link and "linkedin.com/in/" in link:
                urls.append(link)

    urls = list(dict.fromkeys(urls))
    print(f"[DEBUG] URLs finais filtradas: {len(urls)}")
    return urls


def _parse_name_headline_from_title(title: str | None) -> tuple[str | None, str | None]:
    if not title:
        return None, None

    title = html_lib.unescape(title).strip()

    # Exemplos comuns:
    # - "João Silva - LinkedIn"
    # - "João Silva | LinkedIn"
    if " - " in title:
        parts = [p.strip() for p in title.split(" - ") if p.strip()]
    elif " | " in title:
        parts = [p.strip() for p in title.split(" | ") if p.strip()]
    else:
        parts = [title]

    # remove sufixos típicos
    parts = [p for p in parts if p.lower() != "linkedin"]

    if len(parts) >= 2:
        name = parts[0]
        headline = " - ".join(parts[1:]).strip() or None
        return name, headline

    # fallback: tenta separar por "- LinkedIn"
    m = re.match(r"^(.*?)\s*-\s*LinkedIn\s*$", title, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip(), None

    return None, None


def search_profile_candidates(query: str) -> list[dict[str, Any]]:
    """
    Similar ao `search_profile_urls`, mas retorna também `name/headline` usando
    os campos do próprio Serper (que costuma trazer o nome mesmo quando o
    LinkedIn bloqueia o HTML).
    """
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY não encontrado no .env")

    seen: dict[str, dict[str, Any]] = {}

    for page in range(1, 4):
        payload = {"q": query, "gl": "br", "hl": "pt-br", "page": page}
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

        response = requests.post(
            "https://google.serper.dev/search",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            print(f"[ERROR] Serper status={response.status_code}")
            print(f"[ERROR] Resposta: {response.text}")
            break

        data = response.json()
        organic = data.get("organic", [])
        print(f"[DEBUG] Candidates query: {query} | page={page} | resultados={len(organic)}")

        if not organic:
            break

        for item in organic:
            link = item.get("link")
            if not link or "linkedin.com/in/" not in link:
                continue

            linkedin_url = clean_linkedin_url(link)
            if not linkedin_url:
                continue

            name, headline = _parse_name_headline_from_title(item.get("title"))
            # snippet costuma ter "headline" rica, mas só usamos se não houver.
            snippet = (item.get("snippet") or "").strip() or None
            if not headline:
                headline = snippet

            if linkedin_url not in seen:
                seen[linkedin_url] = {
                    "linkedin_url": linkedin_url,
                    "name": name,
                    "headline": headline,
                }

    candidates = list(seen.values())
    print(f"[DEBUG] Candidates finais filtradas: {len(candidates)}")
    return candidates
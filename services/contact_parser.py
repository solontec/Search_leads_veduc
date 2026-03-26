import os
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from utils.http import fetch
from utils.cleaners import clean_text, find_email, find_phone


_SERPER_API_KEY = os.getenv("SERPER_API_KEY")
_SERPER_FALLBACK = os.getenv("SERPER_EMAILPHONE_FALLBACK", "1").strip().lower() in {"1", "true", "yes", "y"}
_SERPER_ENDPOINT = os.getenv("SERPER_ENDPOINT", "https://google.serper.dev/search")
_SERPER_FALLBACK_FETCH_PAGES = int(os.getenv("SERPER_EMAILPHONE_FETCH_PAGES", "3"))


def _extract_social_links(html: str) -> list[str] | None:
    soup = BeautifulSoup(html, "lxml")
    allowed_domains = {
        "twitter.com",
        "x.com",
        "facebook.com",
        "instagram.com",
        "github.com",
        "linkedin.com",
        "youtube.com",
        "youtu.be",
        "tiktok.com",
        "medium.com",
        "medium",
        "dev.to",
        "kaggle.com",
        "angel.co",
        "behance.net",
        "dribbble.com",
        "wa.me",
        "api.whatsapp.com",
    }

    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        # Normaliza esquemas comuns
        if href.startswith("//"):
            href = "https:" + href
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue

        # Remove querystring simples para evitar duplicatas
        href = href.split("#")[0].split("?")[0].strip()

        domain = urlparse(href).netloc.lower()
        if any(d in domain for d in allowed_domains):
            links.add(href)

    if not links:
        return None
    return sorted(links)


def _extract_mail_tel_from_links(html: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(html, "lxml")
    email = None
    phone = None

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if href.startswith("mailto:") and not email:
            candidate = href[len("mailto:") :].split("?")[0].strip()
            email = clean_text(candidate)
        elif href.startswith("tel:") and not phone:
            candidate = href[len("tel:") :].split("?")[0].strip()
            phone = clean_text(candidate)

    return email, phone


def _extract_whatsapp_phone(text: str | None) -> str | None:
    if not text:
        return None

    # wa.me/5511999999999
    m = re.search(r"wa\.me/(\d{8,15})", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # api.whatsapp.com/send?phone=5511999999999
    m2 = re.search(r"(?:api\.whatsapp\.com|wa\.me).{0,100}?phone=([\d\+][\d]{7,15})", text, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).strip()

    return None


def _serper_search_text(query: str, max_results: int = 10) -> str:
    """
    Busca no Serper e retorna um "corpus" de texto (title+snippet+link)
    para rodar regex de email/telefone.
    """
    if not _SERPER_API_KEY:
        return ""

    headers = {"X-API-KEY": _SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "br", "hl": "pt-br", "page": 1}

    try:
        resp = requests.post(_SERPER_ENDPOINT, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"[DEBUG] Serper status={resp.status_code} q={query}")
            return ""
        data = resp.json() or {}
        organic = data.get("organic", [])[:max_results]
        parts: list[str] = []
        for item in organic:
            parts.append(item.get("title") or "")
            parts.append(item.get("snippet") or "")
            parts.append(item.get("link") or "")
        return "\n".join(parts)
    except Exception as exc:
        print(f"[DEBUG] Erro Serper fallback: {type(exc).__name__}: {exc}")
        return ""


def _serper_search_organic(query: str, max_results: int = 10) -> list[dict]:
    if not _SERPER_API_KEY:
        return []

    headers = {"X-API-KEY": _SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "br", "hl": "pt-br", "page": 1}

    try:
        resp = requests.post(_SERPER_ENDPOINT, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"[DEBUG] Serper status={resp.status_code} q={query}")
            return []
        data = resp.json() or {}
        organic = data.get("organic", [])[:max_results]
        return organic if isinstance(organic, list) else []
    except Exception as exc:
        print(f"[DEBUG] Erro Serper fallback organic: {type(exc).__name__}: {exc}")
        return []


def enrich_contacts_from_page(url: str, name: str | None = None) -> dict:
    html = fetch(url)
    if not html:
        return {"email": None, "phone": None, "social_links": None}

    # 1) Tenta extrair do próprio HTML
    email = find_email(html)
    phone = find_phone(html)
    mail_email, mail_phone = _extract_mail_tel_from_links(html)
    email = email or mail_email
    phone = phone or mail_phone
    phone = phone or _extract_whatsapp_phone(html)

    social_links = _extract_social_links(html)

    # 2) Fallback: se LinkedIn bloqueou e não achamos email/phone, busca na web
    #    usando Serper (apenas para tentar achar "lead" acionável).
    if _SERPER_FALLBACK and _SERPER_API_KEY and not email and not phone:
        base = name or url.rstrip("/").split("/")[-1]
        base = re.sub(r"[^A-Za-z0-9_-]+", " ", base).strip()
        if base:
            corpus_parts: list[str] = []
            candidate_links: list[str] = []
            queries = [
                f"\"{base}\" email",
                f"\"{base}\" \"e-mail\"",
                f"\"{base}\" \"@\"",
                f"\"{base}\" telefone",
                f"\"{base}\" whatsapp",
                f"\"{base}\" contato",
                f"\"{base}\" \"tel:\"",
            ]

            print(f"[DEBUG] Serper fallback contacts base={base} linkedin_url={url}")

            for q in queries:
                organic = _serper_search_organic(q)
                for item in organic:
                    candidate_links.append(item.get("link") or "")
                    corpus_parts.append(item.get("title") or "")
                    corpus_parts.append(item.get("snippet") or "")
                    corpus_parts.append(item.get("link") or "")

            corpus = "\n".join(corpus_parts)

            email = email or find_email(corpus)
            phone = phone or find_phone(corpus)
            phone = phone or _extract_whatsapp_phone(corpus)

            # 3) Se ainda faltou, tenta buscar em páginas dos primeiros resultados.
            if not email and not phone and candidate_links:
                unique_links = []
                seen = set()
                for l in candidate_links:
                    l = (l or "").strip()
                    if not l or l in seen:
                        continue
                    seen.add(l)
                    unique_links.append(l)

                for link in unique_links[:_SERPER_FALLBACK_FETCH_PAGES]:
                    if "linkedin.com/in" in link:
                        continue
                    page = fetch(link)
                    if not page:
                        continue
                    if not email:
                        email = find_email(page)
                    if not phone:
                        phone = find_phone(page)
                    phone = phone or _extract_whatsapp_phone(page)
                    if email or phone:
                        break

    return {
        "email": email,
        "phone": phone,
        "social_links": social_links,
    }
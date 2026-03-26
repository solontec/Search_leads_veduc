from bs4 import BeautifulSoup
from db.repository import upsert_lead
from utils.http import fetch
from utils.cleaners import clean_text
import os
import hashlib
import html as html_lib
import re

_DEBUG_PROFILE = os.getenv("DEBUG_PROFILE_HTML", "0").strip().lower() in {"1", "true", "yes", "y"}


def extract_from_title(title: str | None) -> tuple[str | None, str | None]:
    if not title:
        return None, None

    title = html_lib.unescape(title).strip()

    # Ex.: "João Silva - Software Engineer - LinkedIn"
    parts = [p.strip() for p in title.split(" - ") if p.strip()]

    if len(parts) >= 2:
        name = parts[0]
        headline = " - ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
        if headline.lower() == "linkedin":
            headline = None
        return name, headline

    return None, None


def extract_from_meta_description(meta_desc: str | None) -> tuple[str | None, str | None]:
    if not meta_desc:
        return None, None

    meta_desc = html_lib.unescape(meta_desc).strip()

    # tenta separar nome do resto
    # Ex.: "João Silva. Software Engineer. Empresa X ..."
    match = re.match(r"^([^\.]+)\.\s+(.*)$", meta_desc)
    if match:
        name = clean_text(match.group(1))
        headline = clean_text(match.group(2))
        return name, headline

    return None, meta_desc


def parse_public_profile(url: str) -> dict | None:
    print(f"[DEBUG] Baixando perfil: {url}")
    html = fetch(url)

    if not html:
        print(f"[DEBUG] Nenhum HTML retornado para: {url}")
        return None

    # Dump opcional para inspecionar HTML quando o LinkedIn bloqueia.
    if _DEBUG_PROFILE:
        safe_hash = hashlib.sha256(url.encode("utf-8", errors="ignore")).hexdigest()[:12]
        filename = f"debug_profile_{safe_hash}.html"
        try:
            with open(filename, "w", encoding="utf-8", errors="ignore") as f:
                f.write(html)
            print(f"[DEBUG] Debug HTML do perfil salvo em: {filename}")
        except Exception as exc:  # pragma: no cover
            print(f"[DEBUG] Falha ao salvar debug do perfil: {exc}")

    soup = BeautifulSoup(html, "lxml")

    title = clean_text(soup.title.get_text()) if soup.title else None

    meta_desc = None
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta_desc = clean_text(meta.get("content"))

    h1 = soup.find("h1")
    h1_name = clean_text(h1.get_text()) if h1 else None

    name = h1_name
    headline = None

    # 1) tenta pelo h1 + meta
    if name and meta_desc:
        headline = html_lib.unescape(meta_desc)

    # 2) se não achou nome, tenta pelo title
    if not name:
        title_name, title_headline = extract_from_title(title)
        name = title_name or name
        headline = headline or title_headline

    # 3) se ainda não achou, tenta pela meta description
    if not name or not headline:
        meta_name, meta_headline = extract_from_meta_description(meta_desc)
        name = name or meta_name
        headline = headline or meta_headline

    profile = {
        "name": clean_text(name),
        "headline": clean_text(headline),
        "company": None,
        "location": None,
        "linkedin_url": url,
    }

    try:
        upsert_lead(profile)
    except Exception as exc:
        print(f"[ERROR] upsert_lead falhou para linkedin_url={url}: {exc}")
    print(f"[DEBUG] Perfil parseado: {profile}")
    return profile
from bs4 import BeautifulSoup
from utils.http import fetch
from utils.cleaners import clean_text
import html as html_lib

def parse_public_profile(url: str) -> dict | None:
    print(f"[DEBUG] Baixando perfil: {url}")
    html = fetch(url)

    if not html:
        print(f"[DEBUG] Nenhum HTML retornado para: {url}")
        return None

    soup = BeautifulSoup(html, "lxml")

    title = clean_text(soup.title.get_text()) if soup.title else None

    meta_desc = None
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta_desc = clean_text(meta.get("content"))

    h1 = soup.find("h1")
    name = clean_text(h1.get_text()) if h1 else None

    if meta_desc:
        meta_desc = html_lib.unescape(meta_desc)

    if title:
        title = html_lib.unescape(title)

    profile = {
        "name": name,
        "headline": meta_desc or title,
        "company": None,
        "location": None,
        "linkedin_url": url,
    }

    print(f"[DEBUG] Perfil parseado: {profile}")
    return profile
from utils.http import fetch
from utils.cleaners import find_email

def enrich_contacts_from_page(url: str) -> dict:
    html = fetch(url)
    if not html:
        return {"email": None, "phone": None}

    return {
        "email": find_email(html),
        "phone": None
    }
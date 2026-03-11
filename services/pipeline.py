from services.search_service import search_profile_urls
from services.profile_parser import parse_public_profile
from services.contact_parser import enrich_contacts_from_page
from db.repository import upsert_lead

def run_pipeline(query: str):
    urls = search_profile_urls(query)
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] URLs encontradas: {len(urls)}")

    for url in urls:
        print(f"[DEBUG] Processando URL: {url}")

        profile = parse_public_profile(url)
        if not profile:
            print(f"[DEBUG] Falha ao parsear perfil: {url}")
            continue

        # ignora perfis vazios
        if not profile.get("name") and not profile.get("headline"):
            print(f"[DEBUG] Perfil vazio ignorado: {url}")
            continue

        print(f"[DEBUG] Perfil extraído: {profile}")

        contacts = enrich_contacts_from_page(url)
        print(f"[DEBUG] Contatos extraídos: {contacts}")

        lead = {
            **profile,
            **contacts,
            "source": "public_web_search",
            "search_query": query,
            "notes": ""
        }

        print(f"[DEBUG] Salvando lead: {lead}")
        upsert_lead(lead)
from services.search_service import search_profile_candidates
from services.profile_parser import parse_public_profile
from services.contact_parser import enrich_contacts_from_page
from db.repository import upsert_lead
from utils.cleaners import is_valid_email, is_valid_phone

def run_pipeline(query: str):
    try:
        candidates = search_profile_candidates(query)
    except Exception as exc:
        print(f"[ERROR] falha ao buscar URLs para query '{query}': {exc}")
        return

    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Candidates encontradas: {len(candidates)}")

    for candidate in candidates:
        url = candidate["linkedin_url"]
        print(f"[DEBUG] Processando URL: {url}")

        # Começamos com os dados retornados pelo Serper (nome/headline),
        # para não depender 100% do HTML do LinkedIn (que frequentemente bloqueia).
        profile = {
            "name": candidate.get("name"),
            "headline": candidate.get("headline"),
            "company": None,
            "location": None,
            "linkedin_url": url,
        }

        # Tentativa extra: tenta enriquecer via HTML do LinkedIn quando possível.
        try:
            parsed = parse_public_profile(url)
            if parsed:
                for k, v in parsed.items():
                    if v is not None:
                        profile[k] = v
        except Exception as exc:
            print(f"[ERROR] parse_public_profile falhou para {url}: {exc}")

        # Não ignoramos perfis "vazios" porque o `parse_public_profile` já salva pelo
        # menos `linkedin_url`, mas a 2a gravação aqui adiciona metadata e contatos.
        if not profile.get("linkedin_url"):
            print(f"[ERROR] Perfil sem linkedin_url, não será salvo: {url}")
            continue

        print(f"[DEBUG] Perfil extraído: {profile}")

        contacts = enrich_contacts_from_page(url, profile.get("name"))
        print(f"[DEBUG] Contatos extraídos: {contacts}")

        lead = {
            **profile,
            **contacts,
            "source": "public_web_search",
            "search_query": query,
            "notes": ""
        }

        # Filtro para prospects: para prospecção, mantemos apenas leads com email válido.
        # (Caso o lead também tenha phone, melhor, mas não é obrigatório para passar no filtro.)
        has_email = is_valid_email(lead.get("email"))
        has_phone = is_valid_phone(lead.get("phone"))
        if not has_email:
            print(
                f"[DEBUG] Lead ignorado (sem email válido): {lead.get('linkedin_url')} "
                f"name={lead.get('name')} phone_valid={has_phone}"
            )
            continue

        print(f"[DEBUG] Salvando lead: {lead}")
        try:
            upsert_lead(lead)
        except Exception as exc:
            print(f"[ERROR] upsert_lead falhou para linkedin_url={lead.get('linkedin_url')}: {exc}")
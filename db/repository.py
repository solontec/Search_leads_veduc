from datetime import datetime, timezone
from db.mongo import leads
from utils.cleaners import is_valid_email, is_valid_phone

def _normalize_linkedin_url(url: str) -> str:
    url = (url or "").split("?")[0]
    # Normaliza variações de idioma na URL (pt/en) para evitar duplicatas.
    url = url.replace("/pt", "").replace("/en", "")
    return url.rstrip("/")


def upsert_lead(lead: dict):
    if not lead.get("linkedin_url"):
        raise ValueError("Lead inválido: linkedin_url obrigatório")

    now = datetime.now(timezone.utc)

    try:
        lead = dict(lead)  # evita efeitos colaterais na chamada externa
        lead["linkedin_url"] = _normalize_linkedin_url(lead["linkedin_url"])
        if not lead.get("linkedin_url"):
            raise ValueError("Lead inválido: linkedin_url normalizado ficou vazio")

        set_fields = {"updated_at": now}

        # Não sobrescrevemos campos com None; isso evita perder dados já coletados
        # quando uma tentativa posterior falha (ex: LinkedIn bloqueia).
        for field in [
            "name",
            "headline",
            "company",
            "location",
            "phone",
            "email",
            "source",
            "search_query",
            "notes",
            "social_links",
        ]:
            if field in lead and lead.get(field) is not None:
                # Valida campos críticos para evitar lixo no Mongo
                if field == "phone" and not is_valid_phone(lead.get("phone")):
                    continue
                if field == "email" and not is_valid_email(lead.get("email")):
                    continue
                set_fields[field] = lead.get(field)

        result = leads.update_one(
            {"linkedin_url": lead["linkedin_url"]},
            {
                "$set": set_fields,
                "$setOnInsert": {
                    "status": "novo",
                    "created_at": now,
                },
            },
            upsert=True,
        )
    except Exception as exc:
        # Não logamos segredos (MONGO_URI), mas ajuda a localizar o problema no servidor.
        print(
            f"[ERROR] MongoDB upsert falhou para linkedin_url={lead.get('linkedin_url')} "
            f"collection={getattr(leads, 'full_name', 'leads')}: {exc}"
        )
        raise

    print(
        f"[DEBUG] upsert_lead: linkedin_url={lead['linkedin_url']} matched={result.matched_count} modified={result.modified_count} upserted_id={result.upserted_id} set_fields={list(set_fields.keys())}"
    )

    return result
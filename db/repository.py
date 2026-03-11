from datetime import datetime, timezone
from db.mongo import leads

def upsert_lead(lead: dict) -> None:
    now = datetime.now(timezone.utc)

    leads.update_one(
        {"linkedin_url": lead["linkedin_url"]},
        {
            "$set": {
                "name": lead.get("name"),
                "headline": lead.get("headline"),
                "company": lead.get("company"),
                "location": lead.get("location"),
                "phone": lead.get("phone"),
                "email": lead.get("email"),
                "source": lead.get("source"),
                "search_query": lead.get("search_query"),
                "notes": lead.get("notes"),
                "updated_at": now
            },
            "$setOnInsert": {
                "status": "novo",
                "created_at": now
            }
        },
        upsert=True
    )
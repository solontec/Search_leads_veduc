import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")


def search_profile_urls(query: str) -> list[str]:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não encontrado no .env")

    if not GOOGLE_CX:
        raise ValueError("GOOGLE_CX não encontrado no .env")

    urls = []
    start = 1

    # busca até 30 resultados por query (3 páginas de 10)
    while start <= 21:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "start": start,
        }

        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        print(f"[DEBUG] Query: {query} | start={start} | resultados={len(items)}")

        if not items:
            break

        for item in items:
            link = item.get("link")
            if link and "linkedin.com/in/" in link:
                urls.append(link)

        start += 10

    urls = list(dict.fromkeys(urls))
    print(f"[DEBUG] URLs finais filtradas: {len(urls)}")
    return urls
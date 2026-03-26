import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SERPER_API_KEY")

if not api_key:
    raise ValueError("SERPER_API_KEY não encontrado no .env")

headers = {
    "X-API-KEY": api_key,
    "Content-Type": "application/json"
}

payload = {
    "q": 'site:linkedin.com/in "software engineer" "brasil"',
    "gl": "br",
    "hl": "pt-br",
    "page": 1
}

response = requests.post(
    "https://google.serper.dev/search",
    json=payload,
    headers=headers,
    timeout=30
)


print("STATUS:", response.status_code)
print(response.text)
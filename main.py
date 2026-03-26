from services.pipeline import run_pipeline

def load_queries(filepath: str = "queries/queries.txt") -> list[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def main():
    queries = load_queries()

    for query in queries:
        print(f"Rodando query: {query}")
        try:
            run_pipeline(query)
        except Exception as exc:
            print(f"[ERROR] pipeline falhou para '{query}': {exc}")
            # continue with next query

    print("Finalizado.")

if __name__ == "__main__":
    main()
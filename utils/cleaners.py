import re

def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None

def find_email(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None

def find_phone(text: str | None) -> str | None:
    if not text:
        return None
    # Captura strings com cara de telefone, mas com validação extra para não
    # confundir datas (ex: 2026-03-26) como "telefone".
    match = re.search(r"(\+?\d[\d\-\(\)\s/]{6,}\d)", text)
    if not match:
        return None

    candidate = re.sub(r"\s+", " ", match.group(0)).strip()

    # Rejeita padrões claramente de data (YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY etc.)
    cand_no_space = candidate.replace(" ", "")
    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", cand_no_space) or re.fullmatch(
        r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", cand_no_space
    ):
        return None

    digits = re.sub(r"\D", "", candidate)
    # Telefones comuns (padrão BR e variações com DDI) costumam ter 9 a 13 dígitos.
    # 14 dígitos (ex: CNPJ) e acima disso tende a ser "lixo" para prospecção.
    if not (9 <= len(digits) <= 13):
        return None

    # Normaliza para facilitar prospecção: mantem '+' se existir, mas remove
    # parênteses, espaços e hífens.
    normalized = ("+" if "+" in candidate else "") + digits
    return normalized


def is_valid_phone(value: str | None) -> bool:
    return find_phone(value) is not None


def is_valid_email(value: str | None) -> bool:
    return find_email(value) is not None
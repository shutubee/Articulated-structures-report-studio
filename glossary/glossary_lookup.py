import json
from pathlib import Path


def load_glossary():
    path = Path(__file__).with_name("glossary_terms.json")
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_glossary_card(term):
    glossary = load_glossary()
    key = term.strip().lower()
    return glossary.get(key)


def search_glossary(query):
    glossary = load_glossary()
    query = query.strip().lower()

    if not query:
        return list(glossary.values())

    return [
        card
        for key, card in glossary.items()
        if query in key or query in card["definition"].lower()
    ]
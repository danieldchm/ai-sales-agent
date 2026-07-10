"""Ingesta os cases de data/cases/*.json no Qdrant, gerando embeddings via Ollama.

Uso:
    python3 scripts/ingest_cases.py
"""
import glob
import json
import os

import requests

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "ollama.com/library/embeddinggemma:latest")
QDRANT_BASE_URL = os.environ.get("QDRANT_BASE_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "ai_sdr_cases")
CASES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cases")


def embed(text: str) -> list[float]:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": OLLAMA_EMBED_MODEL, "input": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def build_embedding_text(case: dict) -> str:
    partes = [
        case["titulo"],
        case["sintoma_demanda_inicial"],
        " ".join(case.get("sinais_diagnostico", [])),
        case["abordagem_recomendada"],
    ]
    return "\n".join(p for p in partes if p)


def main() -> None:
    paths = sorted(glob.glob(os.path.join(CASES_DIR, "case-*.json")))
    points = []
    for idx, path in enumerate(paths, start=1):
        with open(path, encoding="utf-8") as f:
            case = json.load(f)
        vector = embed(build_embedding_text(case))
        points.append({"id": idx, "vector": vector, "payload": case})
        print(f"[{idx}/{len(paths)}] embedado: {case['id']}")

    resp = requests.put(
        f"{QDRANT_BASE_URL}/collections/{QDRANT_COLLECTION}/points",
        json={"points": points},
        timeout=60,
    )
    resp.raise_for_status()
    print(f"Upsert concluido: {len(points)} pontos na collection '{QDRANT_COLLECTION}'.")


if __name__ == "__main__":
    main()

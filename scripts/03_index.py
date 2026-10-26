# scripts/03_index.py
import json, time, requests, numpy as np
from pathlib import Path

OLLAMA_EMBED = "http://localhost:11434/api/embed"
OLLAMA_EMBED_LEGACY = "http://localhost:11434/api/embeddings"
MODEL = "bge-m3"
BATCH = 16

CHUNKS = Path("data/chunks/chunks.jsonl")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)


def embed_batch(texts):
    payload = {"model": MODEL, "input": texts}
    r = requests.post(OLLAMA_EMBED, json=payload, timeout=900)
    if r.status_code == 404:
        vecs = []
        for t in texts:
            rr = requests.post(OLLAMA_EMBED_LEGACY,
                               json={"model": MODEL, "prompt": t}, timeout=300)
            rr.raise_for_status()
            vecs.append(rr.json()["embedding"])
        return vecs
    r.raise_for_status()
    return r.json()["embeddings"]


def main():
    chunks = [json.loads(l) for l in open(CHUNKS, encoding="utf-8")]
    print(f"chunks to embed: {len(chunks)}")

    vecs = []
    t0 = time.time()

    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        texts = [f"{c['crumb']}\n{c['text']}" for c in batch]
        vecs.extend(embed_batch(texts))
        done = len(vecs)
        speed = done / max(1e-6, time.time() - t0)
        eta = (len(chunks) - done) / max(1e-6, speed)
        print(f"{done}/{len(chunks)}  {speed:.1f} ch/s  ETA {eta/60:.1f} min", flush=True)

    arr = np.asarray(vecs, dtype=np.float32)
    arr /= (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9)

    np.save(INDEX_DIR / "embeddings.npy", arr)

    with open(INDEX_DIR / "meta.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print("saved:", arr.shape)


if __name__ == "__main__":
    main()
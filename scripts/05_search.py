# scripts/05_search.py
import json, re, requests, numpy as np, sys
from pathlib import Path
from rank_bm25 import BM25Okapi

MODEL = "bge-m3"
INDEX_DIR = Path("index")


def tokenize(s):
    return re.findall(r"[\w\+\-]+", s.lower())


class RulesSearch:
    def __init__(self):
        self.meta = [json.loads(l) for l in open(INDEX_DIR / "meta.jsonl", encoding="utf-8")]
        self.emb = np.load(INDEX_DIR / "embeddings.npy")
        self.bm25 = BM25Okapi([tokenize(m["crumb"] + " " + m["text"]) for m in self.meta])

    def embed(self, q):
        r = requests.post("http://localhost:11434/api/embed",
                          json={"model": MODEL, "input": [q]}, timeout=300)
        r.raise_for_status()
        v = np.asarray(r.json()["embeddings"][0], dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-9)

    def search(self, query, k=6):
        qv = self.embed(query)
        sims = self.emb @ qv
        vec_order = np.argsort(-sims)[: k * 6]
        bm_order = np.argsort(-np.asarray(self.bm25.get_scores(tokenize(query))))[: k * 6]
        scores = {}
        for rank, idx in enumerate(vec_order):
            scores[int(idx)] = scores.get(int(idx), 0) + 1 / (60 + rank + 1)
        for rank, idx in enumerate(bm_order):
            scores[int(idx)] = scores.get(int(idx), 0) + 1 / (60 + rank + 1)
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [self.meta[idx] for idx, _ in ranked[:k]]


if __name__ == "__main__":
    s = RulesSearch()
    q = " ".join(sys.argv[1:]) or "difficulty value skill check"
    for m in s.search(q, k=5):
        print("=" * 70)
        print(f"[p{m['page_start']}-{m['page_end']}] {m['crumb']} ({m['kind']})")
        print(m["text"][:700])
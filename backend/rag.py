# backend/rag.py
import json, re, requests, numpy as np, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "bge-m3"


def tokenize(s):
    return re.findall(r"[\w\+\-]+", s.lower())


class RulesSearch:
    def __init__(self):
        print("Loading rules index...", file=sys.stderr, flush=True)
        self.meta = [json.loads(l) for l in open(ROOT / "index/meta.jsonl", encoding="utf-8")]
        print(f"  loaded {len(self.meta)} chunks", file=sys.stderr, flush=True)
        self.emb = np.load(ROOT / "index/embeddings.npy")
        print(f"  loaded embeddings {self.emb.shape}", file=sys.stderr, flush=True)
        try:
            from rank_bm25 import BM25Okapi
            print("  building BM25 index...", file=sys.stderr, flush=True)
            self.bm25 = BM25Okapi([tokenize(m["crumb"] + " " + m["text"]) for m in self.meta])
            print("  BM25 ready", file=sys.stderr, flush=True)
        except Exception:
            self.bm25 = None
        print("Rules search ready", file=sys.stderr, flush=True)

    def embed(self, q):
        r = requests.post("http://localhost:11434/api/embed",
                          json={"model": MODEL, "input": [q]}, timeout=300)
        r.raise_for_status()
        v = np.asarray(r.json()["embeddings"][0], dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-9)

    def search(self, query, k=4):
        qv = self.embed(query)
        vec = np.argsort(-(self.emb @ qv))[: k * 4]
        order = [int(i) for i in vec]
        if self.bm25 is not None:
            bm = np.argsort(-np.asarray(self.bm25.get_scores(tokenize(query))))[: k * 4]
            scores = {}
            for rank, idx in enumerate(order):
                scores[idx] = scores.get(idx, 0) + 1 / (60 + rank + 1)
            for rank, idx in enumerate(int(i) for i in bm):
                scores[idx] = scores.get(idx, 0) + 1 / (60 + rank + 1)
            order = [i for i, _ in sorted(scores.items(), key=lambda x: -x[1])]
        return [self.meta[i] for i in order[:k]]
"""
rank_facts.py ── score & select the best atomicFact sentences for a sub-topic
────────────────────────────────────────────────────────────────────────────
✓ Sentence-BERT for semantic relevance & novelty
✓ News credibility lookup (NewsGuard demo API, transparent cache)
✓ MMR to guarantee diversity among the final k sentences
"""

from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import requests, json, math, hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, util
from src.reasoning.miner.knowledge_miner import KnowledgeModel


SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_encoder   : SentenceTransformer | None = None      # lazy load


def encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(SBERT_MODEL)
    return _encoder


# ---------------------------------------------------------------------------
# 2) credibility (NewsGuard demo – replace with your API key)
# ---------------------------------------------------------------------------

NEWSGUARD_ENDPOINT = "https://api.newsguardtech.com/v1/domain/"
NEWSGUARD_KEY      = "DEMO_KEY"   # put real key in env/secret

@lru_cache(maxsize=512)
def credibility_score(url: str | None) -> float:
    """
    Returns [0,1].  0.5 if url missing or API fails.
    """
    if not url:
        return 0.5
    host = url.split("/")[2]  # naive
    try:
        resp = requests.get(
            NEWSGUARD_ENDPOINT + host,
            headers={"x-api-key": NEWSGUARD_KEY},
            timeout=2,
        )
        data = resp.json()
        return data.get("credibilityScore", 50) / 100.0
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# 3) embeddings helper
# ---------------------------------------------------------------------------

def embed(sent_list: list[str]) -> np.ndarray:
    return encoder().encode(sent_list, convert_to_numpy=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# 4) main ranking routine
# ---------------------------------------------------------------------------

@dataclass
class RankedFact:
    knowledge: KnowledgeModel
    score: float

def rank_facts(
    knowledge: list[KnowledgeModel],
    subtopic: str,
    interest_weight: int,
    already_used: list[str],
    k: int = 5,
    mmr_lambda: float = 0.5,
) -> list[RankedFact]:
    """
    Returns k sentences for the given sub-topic, scored by
        score = interest * credibility * relevance * novelty
    then post-filtered with MMR diversity.
    Returns a list of RankedFact objects containing both the knowledge and its score.
    """
    pool = [f for f in knowledge if f.domain == subtopic]
    if not pool:
        return []

    sentences          = [f.atomicFact.strip() for f in pool]
    sent_emb           = embed(sentences)

    topic_emb          = embed([subtopic])[0]
    used_emb           = embed(already_used) if already_used else np.empty((0,768))

    # cosine similarities (vectorised)
    relevance_vec      = util.cos_sim(sent_emb, topic_emb).squeeze().clip(min=0).numpy()
    novelty_vec        = 1.0 - util.cos_sim(sent_emb, used_emb).max(dim=1).values.clip(min=0).numpy() if used_emb.size else np.ones(len(pool))

    interest_vec       = np.full(len(pool), float(interest_weight))

    # raw *score*
    raw_score          = interest_vec * relevance_vec * novelty_vec

    # ------------------------------------------------------------------ MMR
    selected : list[int] = []
    candidate: set[int]  = set(range(len(pool)))
    final_scores = np.zeros(len(pool))  # Track final MMR scores

    while candidate and len(selected) < k:
        if not selected:
            idx = int(np.argmax(raw_score))
            final_scores[idx] = raw_score[idx]
        else:
            # MMR: maximise λ*relevance − (1−λ)*max_similarity_to_selected
            sim_to_sel = util.cos_sim(sent_emb[list(candidate)], sent_emb[selected]).max(dim=1).values.numpy()
            mmr_score  = mmr_lambda * relevance_vec[list(candidate)] - (1-mmr_lambda) * sim_to_sel
            idx        = list(candidate)[int(np.argmax(mmr_score))]
            final_scores[idx] = mmr_score[int(np.argmax(mmr_score))]
        selected.append(idx)
        candidate.remove(idx)

    return [RankedFact(knowledge=pool[i], score=float(final_scores[i])) for i in selected]


# # ---------------------------------------------------------------------------
# # 5) small demo
# # ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     # ------------ load mock knowledge from json or txt  ----------------
#     raw_json = Path("knowledge.json").read_text(encoding="utf8")
#     knowledge = [KnowledgeModel(**d) for d in json.loads(raw_json)]

#     interest = {"solar": 5, "wind": 10, "geo": 1}
#     already  = ["Global solar capacity reached 1 000 GW in 2022 (+20 %)."]

#     top = rank_facts(
#         knowledge,
#         subtopic="solar",
#         interest_weight=interest["solar"],
#         already_used=already,
#         k=3,
#     )

#     print("\nTop-3 facts for next solar argument\n"+"-"*40)
#     for f in top:
#         sc = credibility_score(f.url)
#         print(f"• {f.atomicFact}  [cred={sc:.2f}]")

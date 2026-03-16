"""Optimized semantic ranking with keyword stuffing penalties"""
import numpy as np
from typing import List, Tuple, Dict, Optional
import io, zipfile, urllib.request, pathlib, sys
from index.builders import create_all_indexes
from index.io import load
from query_processing.query_process import process_query
from utils.text_preprocessing import preprocess

# Ensure repository root is on sys.path when running as a script
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

def get_meta(pkg: Dict) -> Dict:
    # support either "_META_" or "__META__" or nested
    if "_META_" in pkg: return pkg["_META_"]
    if "__META__" in pkg: return pkg["__META__"]
    if "meta_idx" in pkg and "__META__" in pkg["meta_idx"]: return pkg["meta_idx"]["__META__"]
    raise KeyError("Meta section not found in index package.")

def get_unified(pkg: Dict) -> Dict:
    if "unified" in pkg: return pkg["unified"]
    if "unified_ind" in pkg: return pkg["unified_ind"]
    raise KeyError("Unified index not found in index package.")

def df(unified: Dict, term) -> int:
    v = unified.get(term)
    if v is None:
        return 0
    if isinstance(v, (set, list, tuple)):
        return len(v)
    if isinstance(v, dict) and "docs" in v:
        return len(v["docs"])
    return 0
def bm25(
    query_toks: List[str],
    candidate_docs: List[List[str]],
    doc_ids: List[int],
    N: int,
    avgdl: float,
    df_lookup,
    k1: float = 1.2,
    b: float = 0.75,
) -> Tuple[List[int], List[float]]:
    # doc term counts and lengths
    doc_tf: List[Dict[str, int]] = []
    doc_len: List[int] = []
    for tokens in candidate_docs:
        tf: Dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        doc_tf.append(tf)
        doc_len.append(len(tokens))

    q_terms = list(dict.fromkeys(query_toks))  # unique terms, stable

    scores: List[float] = []
    for j in range(len(doc_ids)):
        dl = max(1, doc_len[j])
        norm = k1 * (1 - b + b * (dl / (avgdl if avgdl > 0 else dl)))
        s = 0.0
        tfj = doc_tf[j]
        for t in q_terms:
            tf = tfj.get(t, 0)
            if tf == 0:
                continue
            df = df_lookup(t)
            idf = float(np.log((N - df + 0.5) / (df + 0.5) + 1.0))
            s += idf * ((tf * (k1 + 1.0)) / (tf + norm))
        scores.append(s)

    order = sorted(range(len(doc_ids)), key=lambda i: (-scores[i], doc_ids[i]))
    return [doc_ids[i] for i in order], [scores[i] for i in order]

def tfidf(
    query_toks: List[str],
    candidate_docs: List[List[str]],
    doc_ids: List[int],
    N: int,
    df_lookup,
) -> Tuple[List[int], List[float]]:
    doc_tf: List[Dict[str, int]] = []
    for toks in candidate_docs:
        tf: Dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        doc_tf.append(tf)

    q_terms = list(dict.fromkeys(query_toks))
    scores: List[float] = []
    for j in range(len(doc_ids)):
        tfj = doc_tf[j]
        s = 0.0
        for t in q_terms:
            tf = tfj.get(t, 0)
            if tf == 0:
                continue
            df = df_lookup(t)
            idf = float(np.log(N / (df + 1.0)) + 1.0)
            s += float(np.log(1.0 + tf)) * idf
        scores.append(s)

    order = sorted(range(len(doc_ids)), key=lambda i: (-scores[i], doc_ids[i]))
    return [doc_ids[i] for i in order], [scores[i] for i in order]


def rank_documents(
    query_toks: List[str],
    candidate_docs: List[List[str]],
    doc_ids: List[int],
    inverted_index_path: str,
    method: str = "default"
) -> Tuple[List[int], List[float]]:
    """
    Rank documents using multi-algorithm approach.
    
    Args:
        query_toks: Tokenized and cleaned query terms
        candidate_docs: List of tokenized and cleaned candidate documents
        doc_ids: Document IDs corresponding to candidate_docs
        inverted_index_path: Path to the unified inverted index
        method: Ranking method ("default", ...)
        
    Returns:
        Tuple of (ranked_doc_ids, ranking_scores) - ALL candidates ranked by relevance
    """
    if len(candidate_docs) != len(doc_ids):
        raise ValueError("candidate_docs and doc_ids must have the same length")
    def flatten(seq):
        out = []
        for x in seq:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, (list, tuple)):
                out.extend(str(y) for y in x)
            else:
                out.append(str(x))
        return out

    query_toks = flatten(query_toks)
    candidate_docs = [flatten(d) for d in candidate_docs]

    pkg = load(inverted_index_path)
    meta = get_meta(pkg)
    unified = get_unified(pkg)

    N = int(meta.get("N", 1) or 1)
    avgdl = float(meta.get("avgdl", 0.0) or 0.0)

    def df_lookup(term) -> int:
        return df(unified, term)

    m = method.lower()
    if m in ("default", "bm25"):
        return bm25(query_toks, candidate_docs, doc_ids, N, avgdl, df_lookup)
    elif m == "tfidf":
        return tfidf(query_toks, candidate_docs, doc_ids, N, df_lookup)
    else:
        raise ValueError(f"Unknown ranking method: {method}")


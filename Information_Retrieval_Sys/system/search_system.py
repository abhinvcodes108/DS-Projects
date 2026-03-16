#!/usr/bin/env python3
"""
Command-line Information Retrieval System - Task 4
Usage: python system/search_system.py <queries_json> <documents_jsonl> <run_output_json>
"""
import json, sys, pathlib
import os

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from utils.text_preprocessing import preprocess
from index.builders import create_all_indexes
from query_processing.query_process import process_query
from ranking.rankers import rank_documents

def _load_docs(path):
    """Load documents from JSONL file -> (raw_objs, texts). Keeps first occurrence of each id."""
    docs, texts = [], []
    seen = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
                    continue
                if "id" not in obj or "text" not in obj:
                    print(f"Warning: Line {line_num} missing required fields (id, text)")
                    continue
                did = obj["id"]
                if did in seen:
                    # Keep first instance, as documented
                    print(f"Warning: Duplicate doc_id {did} found, keeping first occurrence")
                    continue
                seen.add(did)
                docs.append(obj)
                texts.append(obj["text"])
    except Exception as e:
        print(f"Error loading documents: {e}")
        sys.exit(1)
    return docs, texts


def _load_queries(path):
    """Load queries from JSON file -> list of {'qid','query'} dicts."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Queries file must be a JSON array")
        out = []
        for i, q in enumerate(data):
            if not isinstance(q, dict) or "qid" not in q or "query" not in q:
                raise ValueError(f"Query {i} missing required fields (qid, query)")
            out.append({"qid": str(q["qid"]), "query": str(q["query"])})
        return out
    except Exception as e:
        print(f"Error loading queries: {e}")
        sys.exit(1)


def _light_morph_expansion(tokens):
    """
    Minimal, deterministic morphology-only expansion (no external libs).
    For each token, add basic base-forms: cats->cat, classes->class, banking->bank, ranked->rank.
    Returns a set of terms (original + expansions).
    """
    def morphs(t):
        out = {t}
        # Simple suffix rules; conservative and order-independent
        if len(t) > 3 and t.endswith("s"):
            out.add(t[:-1])            # cars -> car
        if len(t) > 4 and t.endswith("es"):
            out.add(t[:-2])            # classes -> class
        if len(t) > 5 and t.endswith("ing"):
            out.add(t[:-3])            # banking -> bank
        if len(t) > 4 and t.endswith("ed"):
            out.add(t[:-2])            # ranked -> rank
        return out

    expanded = set()
    for tok in tokens:
        expanded |= morphs(tok)
    return expanded


# ----------------------------- main -----------------------------

def main():
    if len(sys.argv) != 4:
        print("Usage: python system/search_system.py <queries_json> <documents_jsonl> <run_output_json>")
        print("Example: python system/search_system.py data/dev/queries.json data/dev/documents.jsonl runs/run_default.json")
        sys.exit(1)

    queries_path, docs_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    # Mode switches from the output filename (simple on/off flags; no new deps)
    run_name = pathlib.Path(out_path).name.lower()
    ENABLE_QUERY_EXPANSION = ("query_expansion" in run_name)
    AGGRESSIVE_CLEAN = ("data_clean" in run_name)  # actual extra cleaning happens in utils/text_preprocessing.py

    # Expose via env so preprocessing or other modules can read without changing function signatures
    os.environ["ENABLE_QUERY_EXPANSION"] = "1" if ENABLE_QUERY_EXPANSION else "0"
    os.environ["AGGRESSIVE_CLEAN"] = "1" if AGGRESSIVE_CLEAN else "0"
    print(f"[Config] QUERY_EXPANSION={os.environ['ENABLE_QUERY_EXPANSION']}  DATA_CLEAN={os.environ['AGGRESSIVE_CLEAN']}")

    # Load queries and documents
    print(f"Loading queries from: {queries_path}")
    queries = _load_queries(queries_path)
    print(f"Loaded {len(queries)} queries")

    print(f"Loading documents from: {docs_path}")
    raw_docs, doc_texts = _load_docs(docs_path)
    print(f"Loaded {len(raw_docs)} documents")

    # Build (always rebuild) unified index package
    cache_dir = pathlib.Path(__file__).parent.parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    unified_index_path = cache_dir / "unified_package.pkl.gz"

    print("  Creating unified index package...")
    doc_ids = [obj["id"] for obj in raw_docs]
    tokenized_docs = preprocess(doc_texts)
    create_all_indexes(tokenized_docs, str(unified_index_path), doc_ids)

    # Quick access map doc_id -> tokenized doc
    id2toks = {d: toks for d, toks in zip(doc_ids, tokenized_docs)}

    # End-to-end per query
    results = []
    for q in queries:
        qid = q["qid"]
        qstr = q["query"]

        # detect & process structured vs NL resulting in candidate doc IDs
        try:
            candidates = sorted(set(process_query(qstr, str(unified_index_path))))
        except ValueError as ve:
            # Malformed structured query per spec: warn and then keep going with empty candidates
            print(f"Warning: qid={qid} malformed query: {ve}", file=sys.stderr)
            candidates = []
        except Exception as e:
            print(f"Warning: qid={qid} processing error: {e}", file=sys.stderr)
            candidates = []

        # Keep only docs we actually indexed 
        candidates = [d for d in candidates if d in id2toks]

        # Tokenize the query (single-string via batch API)
        q_tokens = preprocess([qstr])[0]

        # Optional non-ranking optimization #1: lightweight expansion BEFORE ranking
        if ENABLE_QUERY_EXPANSION:
            # expand tokens , fetch postings for expanded terms, union with candidates
            expanded_terms = _light_morph_expansion(q_tokens)
            extra = set()
            for term in expanded_terms:
                try:
                    extra.update(get_posting_list(term, str(unified_index_path)))
                except Exception:
                    # term not in vocab or access error -> ignore
                    pass
            # union + keep only indexed doc_ids
            candidates = sorted((set(candidates) | extra) & set(id2toks.keys()))

        # Build candidate docs for ranking
        cand_docs = [id2toks[d] for d in candidates]

        #  ranking (BM25 default inside rank_documents)
        if candidates:
            ranked_ids, scores = rank_documents(
                q_tokens, cand_docs, candidates, str(unified_index_path), method="default"
            )
        else:
            ranked_ids, scores = [], []

        # Keep top-10
        results.append({
            "qid": qid,
            "doc_ids": ranked_ids[:10],
            "scores":  scores[:10],
        })

    # Write output JSON
    print(f"Writing results to: {out_path}")
    out_dir = pathlib.Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Successfully wrote {len(results)} query results")


if __name__ == "__main__":
    main()
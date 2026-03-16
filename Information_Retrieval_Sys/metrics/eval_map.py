#!/usr/bin/env python3
"""
MAP Evaluation Script for Task 4
Evaluates all JSON run files in ./runs/ against development relevance judgments.
Usage: python metrics/eval_map.py
"""

import json
import pathlib
import sys
from collections import defaultdict
JUDGE = pathlib.Path("data/dev/relevance_judge.json")
RUNS  = pathlib.Path("runs")

def load_judge(p: pathlib.Path):
    data = json.load(p.open())
    out = {}
    if isinstance(data, dict):
        for qid, m in data.items():
            out[str(qid)] = {str(d): float(s) for d, s in m.items()}
    elif isinstance(data, list):
        for row in data:
            if not isinstance(row, dict): continue
            qid = str(row.get("qid") or row.get("id") or row.get("query_id"))
            if not qid: continue
            m = None
            for k in ("judgments","rels","relevance","labels","relevance_scores"):
                if isinstance(row.get(k), dict):
                    m = row[k]; break
            if m is None and "doc_ids" in row and "scores" in row:
                m = {str(d): float(s) for d,s in zip(row["doc_ids"], row["scores"])}
            out[qid] = {str(d): float(s) for d,s in (m or {}).items()}
    else:
        raise ValueError("Unsupported judge format")
    return out

def load_run(p: pathlib.Path):
    """Return {qid: [doc_id,...]} from common run formats."""
    data = json.load(p.open())
    runs = {}
    if isinstance(data, dict):
        for qid, arr in data.items():
            lst = []
            arr = arr if isinstance(arr, list) else [arr]
            for it in arr:
                if isinstance(it, dict):
                    did = it.get("doc_id") or it.get("id")
                    if did is not None: lst.append(str(did))
                else:
                    lst.append(str(it))
            runs[str(qid)] = lst
    elif isinstance(data, list):
        for row in data:
            if not isinstance(row, dict): continue
            qid = row.get("qid") or row.get("id") or row.get("query_id")
            if qid is None: continue
            if "results" in row and isinstance(row["results"], list):
                runs[str(qid)] = [str(it.get("doc_id") or it.get("id")) for it in row["results"] if isinstance(it, dict)]
            elif "doc_ids" in row:
                runs[str(qid)] = [str(d) for d in row["doc_ids"]]
            elif "ranked" in row:
                runs[str(qid)] = [str(d) for d in row["ranked"]]
    else:
        raise ValueError(f"Unsupported run format in {p}")
    return runs

def average_precision(ranked, relmap):
    """AP for one query; rel if relmap[doc]>0."""
    rel = {d for d, s in relmap.items() if s > 0}
    if not rel: return 0.0
    hits = 0; acc = 0.0
    for i, d in enumerate(ranked, 1):
        if d in rel:
            hits += 1
            acc  += hits / i
    return acc / len(rel)

def mean_average_precision(run, judge):
    """MAP across all judged queries (missing qids count as AP=0)."""
    if not judge: return 0.0
    return sum(average_precision(run.get(qid, []), rels) for qid, rels in judge.items()) / len(judge)

def main():
    if not JUDGE.exists():
        print(f"ERROR: missing {JUDGE}", file=sys.stderr); sys.exit(1)
    if not RUNS.exists():
        print(f"ERROR: missing {RUNS}/", file=sys.stderr); sys.exit(1)

    judge = load_judge(JUDGE)
    run_files = sorted(RUNS.glob("*.json"))
    if not run_files:
        print("No runs found in ./runs/", file=sys.stderr); sys.exit(1)

    print(f"{'Run file':35s}  {'MAP':>8s}")
    print("-" * 46)
    for rf in run_files:
        try:
            run = load_run(rf)
            m = mean_average_precision(run, judge)
            print(f"{rf.name:35s}  {m:8.3f}")
        except Exception as e:
            print(f"{rf.name:35s}  ERROR: {e}")

if __name__ == "__main__":
    main()
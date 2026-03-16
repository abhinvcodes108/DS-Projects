from typing import Set, List, Union
import re
from index.access import get_term_positions, get_posting_list

Key = Union[str, tuple]

near_reg = re.compile(r'^\s*(?P<L>(?:"[^"]+"|\w+))\s+NEAR/(?P<K>\d+)\s+(?P<R>(?:"[^"]+"|\w+))\s*$')

def process_proximity_query(query: str, index_path: str) -> Set[int]:
    """
    Process proximity queries with NEAR/k semantics.
    
    Args:
        query: Proximity query (e.g., "climate NEAR/3 change", '"machine learning" NEAR/2 algorithms')
        index_path: Path to the unified index package
        
    Returns:
        Set of document IDs where operands satisfy NEAR/k distance constraint
        
    NEAR/k semantics:
    - Distance D = min(|q_start - p_end|, |p_start - q_end|)
    - Document satisfies NEAR/k iff D <= k for some occurrence pair
    - Edge-to-edge distance, order-insensitive
    """

    m = near_reg.match(query)
    if not m:
        return set()  # detection should prevent malformed queries
    k = int(m.group("K"))
    Ltok = m.group("L")
    Rtok = m.group("R")

    Lkey, Llen = key_and_len(Ltok)
    Rkey, Rlen = key_and_len(Rtok)

    return satisfying_docs(k, Lkey, Llen, Rkey, Rlen, index_path)


def key_and_len(tok: str) -> tuple[Key, int]:
    """Return (index key, token length). Phrases -> tuple key; terms -> str key."""
    if tok.startswith('"') and tok.endswith('"'):
        parts = [p for p in tok[1:-1].split() if p]
        return (parts[0] if len(parts) == 1 else tuple(parts)), len(parts)
    return tok, 1

def edge_distance(ls: int, le: int, rs: int, re_: int) -> int:
    """Edge-to-edge distance D as defined (order-insensitive)."""
    if re_ < ls:
        return ls - re_
    if le < rs:
        return rs - le
    return 0  # overlapping spans

def satisfying_docs(k: int, Lkey: Key, Llen: int, Rkey: Key, Rlen: int, index_path: str) -> Set[int]:
    Ldocs = set(get_posting_list(Lkey, index_path))
    Rdocs = set(get_posting_list(Rkey, index_path))
    cand = Ldocs & Rdocs
    out: Set[int] = set()

    for d in cand:
        Lpos: List[int] = sorted(get_term_positions(Lkey, d, index_path))
        Rpos: List[int] = sorted(get_term_positions(Rkey, d, index_path))
        if not Lpos or not Rpos:
            continue

        Lspans = [(p, p + Llen - 1) for p in Lpos]
        Rspans = [(q, q + Rlen - 1) for q in Rpos]

        ok = False
        for ls, le in Lspans:
            for rs, re_ in Rspans:
                # same exact span cannot satisfy both operands
                if ls == rs and le == re_:
                    continue
                if edge_distance(ls, le, rs, re_) <= k:
                    ok = True
                    break
            if ok:
                break
        if ok:
            out.add(d)
    return out
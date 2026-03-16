"""
Unified Index Package Builder - Task 1
Creates a single on-disk package containing all three sub-indexes.
"""

from typing import List, Dict, Union, Tuple, Any, Optional
from collections import defaultdict
from utils.ngram import make_ngrams_tokens, make_ngrams_chars
from utils.positions import make_positions
from .io import dump

def _ddlist():
    return defaultdict(list)

def create_all_indexes(
    tokenized_docs: List[List[str]], 
    index_path: str, 
    doc_ids: Optional[List[int]] = None
) -> None:
    """
    Build a unified index package containing all three sub-indexes in a single pass.
    
    Args:
        tokenized_docs: List of tokenized documents, each document is a list of tokens
        index_path: Path where the unified index package will be saved
        doc_ids: Optional list of document IDs. If None, uses sequential IDs (0, 1, 2, ...)
                 Must be same length as tokenized_docs if provided.
    """
    Key = Union[str, Tuple[str, ...]]

    max_tkn = 3
    max_char = 3

    unified: Dict[Key, set[int]] = defaultdict(set)
    proximity: Dict[Key, Dict[int, List[int]]] = defaultdict(_ddlist)
    wildcard: Dict[str, set[str]] = defaultdict(set)

    # FIX: doc_lengths must be a dict; N/avgdl will be filled after the loop
    meta_idx = {"__META__": {"N": 0, "avgdl": 0.0, "doc_lengths": {}}}

    # precompute doc IDs
    if doc_ids is not None:
        if len(doc_ids) != len(tokenized_docs):
            raise ValueError("doc_ids must be the same length as tokenized_docs")
        doc_ids_iter = doc_ids
    else:
        doc_ids_iter = list(range(len(tokenized_docs)))

    total_len = 0

    for i, tokens in enumerate(tokenized_docs):
        d_id = doc_ids_iter[i]
        dl = len(tokens)
        meta_idx["__META__"]["doc_lengths"][d_id] = dl
        total_len += dl

        # unified & proximity
        for n in range(1, max_tkn + 1):
            tkn_ngrams = make_positions(tokens, n)  # expects {tuple(token,...): [pos,...]}
            if not tkn_ngrams:
                continue

            for x, pos in tkn_ngrams.items():
                k: Key = x[0] if n == 1 else x  # unigram -> str, n>1 -> tuple
                unified[k].add(d_id)
                if pos:
                    proximity[k][d_id].extend(pos)

                # wildcard only for unigrams
                if n == 1:
                    word = k  # type: ignore[assignment]
                    for char in make_ngrams_chars(word, max_char):
                        if char and char != "$":
                            wildcard[char].add(word)

    # fill meta
    N = len(tokenized_docs)
    meta_idx["__META__"]["N"] = N
    meta_idx["__META__"]["avgdl"] = (total_len / N) if N else 0.0

    # package and save
    package = {
        "unified": unified,
        "proximity": proximity,
        "wildcard": wildcard,
        "meta_idx": meta_idx,
    }
    dump(package, index_path)
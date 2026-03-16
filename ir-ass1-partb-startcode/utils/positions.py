"""Token-position mapping (Task A-2)."""
from collections import defaultdict
from typing import Dict, List, Union, Tuple
import nltk

def make_positions(tokens: List[str], n: int = 1) -> Dict[Tuple[str, ...], List[int]]:
    """
    Map each token n-gram to a list of 0-based start positions.
    Uses NLTK ngrams; coerces keys to tuples of strings (hashable).
    """
    out: Dict[Tuple[str, ...], List[int]] = {}
    L = len(tokens)
    if n <= 0 or L < n:
        return out

    grams = list(nltk.ngrams(tokens, n))  # yields successive n-grams
    for start, gram in enumerate(grams):
        # Ensure the dict key is hashable and uniform
        if not isinstance(gram, tuple):
            gram = tuple(gram)
        gram = tuple(str(x) for x in gram)

        out.setdefault(gram, []).append(start)

    return out
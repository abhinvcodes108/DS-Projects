from typing import Set
from index.access import find_wildcard_matches, get_posting_list


MAX_CHAR_N = 3  # matches your builder

def process_wildcard_query(pattern: str, index_path: str) -> Set[int]:
    """
    Process wildcard queries using character n-grams.
    
    Args:
        pattern: Wildcard pattern (e.g., "climat*", "*tion", "learn*ing")
        index_path: Path to the unified index package
        
    Returns:
        Set of document IDs containing terms matching the pattern
    """
    grams = pattern_grams(pattern)
    if not grams:
        # With 2-3-gram indexing, very short patterns like "a*" provide no grams.
        # return empty by design (assignment examples use longer stems).
        return set()

    # Intersect candidate term sets from the wildcard sub-index
    candidates = None  # start with no seed
    for g in grams:
        terms = set(find_wildcard_matches(g, index_path))
        if not terms:           # skip grams not present in the index
            continue
        if candidates is None:  # first non-empty gram becomes the seed
            candidates = terms
        else:
            candidates &= terms
        if not candidates:      # early exit if intersection empties
            return set()

    if candidates is None:      # all grams were missing
        return set()

    # Final verification against the actual wildcard pattern (no regex)
    verified = [t for t in candidates if matches(pattern, t)]
    if not verified:
        return set()

    # Union postings for all verified terms
    docs: Set[int] = set()
    for t in verified:
        docs |= set(get_posting_list(t, index_path))
    return docs

def pattern_grams(pattern: str):
    """
    Build candidate character n-grams (length 2..3).
    - Internal grams from each non-empty segment between '*'s.
    - Add $-anchored grams if pattern is anchored at start/end.
    """
    grams = []
    segs = pattern.split("*")
    anchored_start = not pattern.startswith("*")
    anchored_end = not pattern.endswith("*")

    # Internal grams from each segment
    for seg in segs:
        L = len(seg)
        for n in (2, 3):
            if L >= n:
                for i in range(L - n + 1):
                    grams.append(seg[i:i + n])

    # Boundary grams (only if anchored and segment long enough)
    if anchored_start and segs and segs[0]:
        first = segs[0]
        for n in (2, 3):
            if len(first) >= n:
                grams.append("$" + first[:n])
    if anchored_end and segs and segs[-1]:
        last = segs[-1]
        for n in (2, 3):
            if len(last) >= n:
                grams.append(last[-n:] + "$")

    # Dedupe preserving order
    out, seen = [], set()
    for g in grams:
        if g not in seen:
            seen.add(g)
            out.append(g)
    return out

def matches(pattern: str, term: str) -> bool:
    """
    Manual wildcard match (only '*' is special).
    - '*' matches any sequence (including empty)
    - Start/end anchoring is implied by lack/presence of leading/trailing '*'
    """
    segs = pattern.split("*")
    anchored_start = not pattern.startswith("*")
    anchored_end = not pattern.endswith("*")

    # Handle trivial all 
    if all(s == "" for s in segs):
        return False

    pos = 0

    # First segment
    if segs:
        first = segs[0]
        if first:
            if anchored_start:
                if not term.startswith(first):
                    return False
                pos = len(first)
            else:
                idx = term.find(first, pos)
                if idx == -1:
                    return False
                pos = idx + len(first)

    # Middle segments
    for seg in segs[1:-1]:
        if seg == "":
            continue
        idx = term.find(seg, pos)
        if idx == -1:
            return False
        pos = idx + len(seg)

    # Last segment
    if len(segs) >= 2:
        last = segs[-1]
        if last:
            if anchored_end:
                if not term.endswith(last):
                    return False
                # ensure the end-occurrence is not before pos
                start_at_end = len(term) - len(last)
                if start_at_end < pos:
                    return False
            else:
                idx = term.find(last, pos)
                if idx == -1:
                    return False
        else:
            # pattern ends with '*': ok
            pass

    return True

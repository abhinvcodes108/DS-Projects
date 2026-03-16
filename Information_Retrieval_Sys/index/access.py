"""
Unified Index Package Access Functions - Task 1
Provides O(1) access to all three sub-indexes from a single package.
"""

from typing import List, Union, Tuple, Dict, Any
from .io import load
import re

Key = Union[str, Tuple[str, ...]]
# Global cache to store loaded packages for O(1) access
_package_cache: Dict[str, Dict[str, Any]] = {}

def _load_package(index_path: str) -> Dict[str, Any]:
    """Load and cache the unified index package."""
    if index_path not in _package_cache:
        _package_cache[index_path] = load(index_path)
    return _package_cache[index_path]

def _norm(term: Key) -> Key:
    # accept list/tuple/str; store unigrams as str, n>=2 as tuple
    if isinstance(term, list):
        term = tuple(term)
    return term

def get_posting_list(term: Union[str, Tuple[str, ...]], index_path: str) -> List[int]:
    """
    Returns the posting list for a unigram or n-gram from the unified sub-index.
    
    Args:
        term: A string (unigram) or tuple of strings (n-gram)
        index_path: Path to the unified index package
        
    Returns:
        List of document IDs (sorted, deduplicated) containing the term
    """
    package = _load_package(index_path)
    unified_index = package.get("unified", {})
    return list(unified_index.get(_norm(term), []))

def find_wildcard_matches(ngram: str, index_path: str) -> List[str]:
    """
    Returns the terms for an character n-grams.
    
    Args:
        ngram: an n-gram (e.g., "$cl", "on$")
        index_path: Path to the unified index package
        
    Returns:
        List of matching terms (sorted lexicographically, deduplicated)
    """
    package = _load_package(index_path)
    wildcard_index = package.get("wildcard", {})
    return list(wildcard_index.get(ngram, []))


def get_term_positions(term: Union[str, Tuple[str, ...]], doc_id: int, index_path: str) -> List[int]:
    """
    Returns the position list for a unigram or n-gram in a specific document.
    
    Args:
        term: A string (unigram) or tuple of strings (n-gram)
        doc_id: Document ID
        index_path: Path to the unified index package
        
    Returns:
        List of positions (0-based, sorted, deduplicated) where the term appears in the document
    """
    package = _load_package(index_path)
    proximity_index = package.get("proximity", {})
    return list(proximity_index.get(_norm(term), {}).get(int(doc_id), []))
    

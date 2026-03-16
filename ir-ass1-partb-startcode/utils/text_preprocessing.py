"""Robust HTML→tokens cleaning pipeline (Task A-1)."""
import re, html, unicodedata
from typing import List, Union
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize



__all__ = ["preprocess"]


def preprocess(raw_html_list: List[str]) -> List[List[str]]:
   
    texts = list(raw_html_list or [])
    if not texts:
        return []

    pat = re.compile(r"[^a-zA-Z.!]+")  # keep letters, '.' and '!' ; collapse others to a single space
    token_lists: List[List[str]] = []

    for x in texts:
        s = x if isinstance(x, str) else str(x)
        s = BeautifulSoup(s, "html.parser").get_text()
        s = html.unescape(s)
        s = pat.sub(" ", s).lower().strip()
        toks = word_tokenize(s) if s else []
        token_lists.append(toks)

    return token_lists


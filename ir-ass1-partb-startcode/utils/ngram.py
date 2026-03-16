"""Word- and char-level n-gram helpers (Task A-2)."""
from typing import List, Tuple
import nltk

__all__ = ["make_ngrams_tokens", "make_ngrams_chars"]


def make_ngrams_tokens(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    if not isinstance(n, int): 
        raise TypeError("n must be an int") # is n is not an integer it raises an exception
    if n <= 0:
        return [] #if n<0 the function returns empty list
    tokens= ["<s>"]+tokens+["</s>"] # adding /s to the beginning and end of tokens for padding
    ngrams=list(nltk.ngrams(tokens,n)) #generating word level ngrams of the tokens
    return ngrams #returning ngrams
    pass

def make_ngrams_chars(text: str, n: int) -> List[str]:
    if not isinstance(n, int):
        raise TypeError("n must be an int") # is n is not an integer it raises an exception
    if n <= 0:
        return [] #if n<0 the function returns empty list
    ngrams=list(nltk.ngrams("$"+text+"$",n))  #pdding the token with /s in the beginning and end
    ngrams=["".join(x) for x in ngrams] #generating character level ngrams of the token
    return ngrams #returning character level ngrams
    pass




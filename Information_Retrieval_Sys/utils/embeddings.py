"""Light-weight GloVe loader & semantic aggregation (Task A-4)."""
import io, zipfile, urllib.request, pathlib
from typing import Dict, List, Tuple

import numpy as np

_GLOVE_URL  = ("http://nlp.stanford.edu/data/glove.6B.zip", "glove.6B.100d.txt")
_CACHE      = pathlib.Path.home() / ".cache" / "ir_glove_100.txt"


def _ensure_glove() -> Dict[str, np.ndarray]:
    if not _CACHE.exists():
        url, fname = _GLOVE_URL
        with urllib.request.urlopen(url) as resp:
            with zipfile.ZipFile(io.BytesIO(resp.read())) as zf:
                _CACHE.write_text(zf.read(fname).decode())

    vocab = {}
    with _CACHE.open() as f:
        for line in f:
            word, *vec = line.strip().split()
            vocab[word] = np.asarray(vec, dtype=float)

    # deterministic random <unk> – keeps load fast
    if "<unk>" not in vocab:
        rng = np.random.default_rng(seed=42)
        dim = len(next(iter(vocab.values())))
        vocab["<unk>"] = rng.normal(0.0, 0.05, size=dim)

    return vocab


_WORD_VEC: Dict[str, np.ndarray] = _ensure_glove()
_DIM: int = next(iter(_WORD_VEC.values())).shape[0]


def _key(tok: str) -> str:
    """Return token itself if in vocab, else '<unk>'."""
    return tok if tok in _WORD_VEC else "<unk>"

def semantic_vector(docs: List[List[str]], method: str = "mean") -> np.ndarray:
    """
    Parameters
    ----------
    docs   : list of token lists
    method : "mean" | "max" | "sum" | "tfidf_weighted" | "meanmax"
    Please remove your cached glove file when you submitting your code
    """
    
    docs = [[word.lower() for word in doc] for doc in docs] #converting the documents to lower case
    doc_freq: Dict[str, int] = {} #creting a dictionery to record doc frequency

    out_embeddings=[] #list to store embeddings
    if method in ("mean", "max", "sum","meanmax"): #checking if the method is valid
      for doc in docs:
        embs = [ _WORD_VEC[_key(t)] for t in doc ] #adding embedding for each document into emb
    
        if not embs:
                # if the embeddings for the word is absent,the output emddings are populated with zeroes
                out_embeddings.append(
                    np.zeros(2 * _DIM if method == "meanmax" else _DIM) 
                )
                continue
        embeddings_array = np.vstack(embs) #the list of embeddings is converted into an array
        # we are pooling the 2d array of embeddings into one vector per document
        if method == 'mean': #averaging over the tokens
          out_embeddings.append(np.mean(embeddings_array, axis=0))
        elif method == 'max': #element wise maximum over the tokens
          out_embeddings.append(np.max(embeddings_array, axis=0))
        elif method == 'sum': #element wise sum over the tokens
          out_embeddings.append(np.sum(embeddings_array, axis=0))
        elif method == "meanmax": #concatination of mean and max
          mean_v = embeddings_array.mean(axis=0)                
          max_v  = embeddings_array.max(axis=0)               
          out_embeddings.append(np.concatenate([mean_v, max_v], axis=0)) 
      
      return np.vstack(out_embeddings) #converting the pooled embeddings into array
      
    if method == "tfidf_weighted":
      tf_mode = "raw"
      try:
          from tfidf import tfidf_variants #importing the tfidf_variants method from the tfidf.py file
      except ImportError as e: #exception handling in case of missing file
          raise ImportError( 
              "Could not import tfidf_variants from tfidf.py.") from e
      tf_idf_vals, vocab_index = tfidf_variants(docs, tf_mode=tf_mode) #calculating the tf idf values of documents

      vocab_terms = [None] * len(vocab_index) #turns the vocab dictionery into a list ordered by index
      for word, j in vocab_index.items():
          vocab_terms[j] = word


      embs= np.vstack([_WORD_VEC[_key(t.lower())] for t in vocab_terms]) #creating  array of embeddings for the vocab terms
      
      nume = tf_idf_vals @ embs # calculating the matrix multiplication  of tfidf values and embeddings
      denom = tf_idf_vals.sum(axis=1, keepdims=True)
      denom[denom == 0] = 1.0    #inorder to prevent divide by zero

      return nume/denom   
    
    raise ValueError("Unknown method. Use 'mean', 'max', 'sum', 'meanmax' or 'tfidf_weighted'")

    pass




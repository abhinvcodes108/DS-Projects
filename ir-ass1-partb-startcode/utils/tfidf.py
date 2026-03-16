"""TF-IDF variants (Task A-3)."""
import math, numpy as np
from typing import List, Dict, Tuple

def tfidf_variants(
        docs: List[List[str]],
        tf_mode: str = "raw",
        k: float = 1.2
) -> Tuple[np.ndarray, Dict[str, int]]:
    # TODO: Implement the TF-IDF variants
    vocab=set() #creating a set of vocabulary terms
    vocab_dict={} #creating a dictionery of vocab terms with thier indices
    idf_vals={} #dictionery for storing tokens and thier idf values
    docs_lower = [[word.lower() for word in doc] for doc in docs] #converting the list of documents into lower case

    for doc in docs_lower:
      vocab.update(doc) #adding words from the documents to the vocabulary set
    sort_vocab=sorted(vocab) #sorting the vocabulary
    for x,y in enumerate(sort_vocab):
      vocab_dict[y]=x # adding the vocab terms and their indices to the dictionery

    doc_len=len(docs_lower) #total number of documents
    vocab_size=len(vocab) #total size of vocabulary

    for word in sort_vocab: #iterating through each word in the vocab
      docs_with_word = sum(1 for doc in docs_lower if word in doc) #counting how many documents has the word
      idf_vals[word] = math.log(doc_len / docs_with_word) #calcuating idf value for the word and storing it in the dictionery

    
    vectors = np.zeros((len(docs_lower), vocab_size)) #creating zero vector with the dimensions of 'number of documents X number of words in vocab'

    for idx,doc in enumerate(docs_lower): #iterating through each document
      d=len(doc) #length of the document
      if d==0: #if document length is zero we skip the document as we can't divide by zero for TF
        continue
      for word in sort_vocab: #iterating through each word in vocab
        tf= doc.count(word)/d #calculating tf values for each word in the vocab for each document

        if tf_mode=="log": #of tf_mode is log
                if tf>0:
                        tf=1+math.log(tf) #calculates tf values according to log formula. Returns zero is tf<0
            
        elif tf_mode=="bm25": #calculates tf according to bm25 formula
                tf=(tf*(k+1))/(k+tf)
        
        elif tf_mode=="raw": #calculates raw tf values
                tf=tf
      
        vectors[idx,vocab_dict[word]]=tf*idf_vals[word]  #populates vector with tf idf values 
        
    return vectors,vocab_dict #returns tfidf vector and vocabulary with index
        
    pass

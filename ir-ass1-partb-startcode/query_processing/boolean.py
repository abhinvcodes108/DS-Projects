from typing import Set, List, Union
from index.access import get_posting_list
import re

def process_boolean_query(query: str, index_path: str) -> Set[int]:
    """
    Process Boolean queries with AND/OR/NOT operators, parentheses, and quoted phrases.
    
    Args:
        query: Boolean query string with operators and optional quotes/parentheses
        index_path: Path to the unified index package
        
    Returns:
        Set of document IDs matching the boolean query
        
    Precedence: NOT > AND > OR
    Supports parentheses and quoted phrases
    """
    token_re = re.compile(r'"[^"]+"|\(|\)|AND|OR|NOT|\w+', re.IGNORECASE)
    tokens: List[str] = token_re.findall(query)
    tokens = [t.upper() if t.upper() in {"AND","OR","NOT"} else t for t in tokens]

    if not tokens:
        return set()

    i, n = 0, len(tokens)

    def peek() -> str | None:
        return tokens[i] if i < n else None

    def eat(expected: str | None = None) -> str:
        nonlocal i
        if i >= n:
            raise ValueError("Unexpected end of query.")
        t = tokens[i]
        if expected is not None and t.upper() != expected:
            raise ValueError(f"Expected '{expected}', found '{t}'.")
        i += 1
        return t

    def postings(tok: str) -> Set[int]:
        if tok.startswith('"') and tok.endswith('"'):
            parts = tok[1:-1].split()
            parts = [p.lower() for p in parts]
            
            try:
                return set(get_posting_list(tuple(parts), index_path))
            except Exception:
                # fallback: AND the single-term postings
                acc: Set[int] | None = None
                for p in parts:
                    s = set(get_posting_list(p, index_path))
                    acc = s if acc is None else (acc & s)
                return acc or set()
        # single term
        return set(get_posting_list(tok.lower(), index_path))

   

    def parse_expr() -> Set[int]:
        res = parse_term()
        while peek() == "OR":
            eat("OR")
            res |= parse_term()
        return res

    def parse_term() -> Set[int]:
        res = parse_operand()
        while True:
            t = peek()
            if t == "AND":
                eat("AND")
                if peek() == "NOT":
                    eat("NOT")
                    res -= parse_operand()          # A AND NOT B  -> A \ B
                else:
                    res &= parse_operand()          # A AND B
            elif t == "NOT":
                # Support 'A NOT B' (difference) as per examples
                eat("NOT")
                res -= parse_operand()
            else:
                break
        return res

    def parse_operand() -> Set[int]:
        t = peek()
        if t is None:
            return set()
        if t == "(":
            eat("(")
            res = parse_expr()
            eat(")")
            return res
        # Disallow operators as operands
        if t in {"AND","OR","NOT",")"}:
            raise ValueError("Two operators in a row.")
        eat()  # consume the term/phrase token
        return postings(t)
    result = parse_expr()
    if peek() is not None:
        raise ValueError("Malformed boolean query (extra tokens).")
    return result

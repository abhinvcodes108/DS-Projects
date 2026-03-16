import re

def detect_query_type(query: str) -> str:
    """
    Detect query type based on case-sensitive syntax keywords.
    
    Args:
        query: Input query string
        
    Returns:
        Query type: "proximity", "wildcard", "boolean", or "natural_language"
    """
    q = query.strip()

    # basic malformed checks shared by structured queries
    checking_parentheses(q)
    checking_matched_quotes(q)

    # Proximity
    if "NEAR/" in q:
        # mixed types not allowed
        if "*" in q or bool(re.search(r'\b(AND|OR|NOT)\b', q)):
            raise ValueError("Mixed proximity with wildcard/boolean is not allowed.")
        # exactly one NEAR/k
        if len(re.findall(r'NEAR/', q)) != 1:
            raise ValueError("More than one NEAR/k.")
        # strict NEAR/k form and operands: single term or quoted phrase
        m = re.fullmatch(r'\s*(?P<left>(?:"[^"]+"|\w+))\s+NEAR/(?P<k>\d+)\s+(?P<right>(?:"[^"]+"|\w+))\s*', q)
        if not m:
            raise ValueError("Malformed NEAR/k form or operands.")
        # k must be integer (regex enforces digits) and non-negative
        # phrases already checked (<=3 words)
        return "proximity"

    # Wildcard 
    if "*" in q:
        # must be a single token containing '*' and at least one non-* char
        if bool(re.search(r'\b(AND|OR|NOT)\b', q)) or '"' in q or "NEAR/" in q:
            raise ValueError("Mixed wildcard with other operators is not allowed.")
        tok = q.strip()
        if any(ch.isspace() for ch in tok):
            raise ValueError("Wildcard must be a single token.")
        if re.fullmatch(r'\*+', tok):
            raise ValueError("Wildcard must include at least one non-* character.")
        return "wildcard"

    # Boolean (operators or matched quotes) 
    if bool(re.search(r'\b(AND|OR|NOT)\b', q)) or '"' in q:
        # NOT alone
        if re.fullmatch(r'\s*NOT\s*', q):
            raise ValueError("NOT cannot appear alone.")
        # leading/trailing operator
        if re.match(r'^\s*(AND|OR|NOT)\b', q) or re.search(r'\b(AND|OR|NOT)\s*$', q):
            raise ValueError("Leading/trailing operator.")
        # two operators in a row
        if re.search(r'\b(AND|OR|NOT)\b\s+\b(AND|OR|NOT)\b', q):
            raise ValueError("Two operators in a row.")
        # unknown ALL-CAPS operators
        for op in re.findall(r'\b[A-Z]{2,}\b', q):
            if not re.fullmatch(r'(AND|OR|NOT|NEAR/\d+)', op):
                raise ValueError(f"Unknown operator: {op}")
        return "boolean"

    # Natural language 
    return "natural language"
    
    
def checking_matched_quotes(q: str) -> None:
    if q.count('"') % 2 != 0:
        raise ValueError("Unmatched quotes.")
    # empty phrase
    if '""' in q:
        raise ValueError("Empty phrase \"\" is malformed.")
    # phrase length limit (<= 3 words)
    for ph in re.findall(r'"([^"]+)"', q):
        if len(ph.split()) > 3:
            raise ValueError("Phrase longer than 3 words is malformed.")

def checking_parentheses(q: str) -> None:
    depth = 0
    in_quote = False
    for ch in q:
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth < 0:
                    raise ValueError("Unbalanced parentheses.")
    if depth != 0:
        raise ValueError("Unbalanced parentheses.")
    if re.search(r'\(\s*\)', q):
        raise ValueError("Empty parentheses ().")
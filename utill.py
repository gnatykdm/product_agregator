def replace_spaces(s: str) -> str:
    if not s:
        raise ValueError("Input prompt cannot be empty")
    
    return s.replace(" ", "+")
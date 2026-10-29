import re

# Comprehensive safety blocklist for slurs, hate speech, and real-world threats
# Friendly gaming banter and mild swear words (shit, damn, fuck, hell, bruh, clown, etc.) are allowed in banter/full_gamer
PROHIBITED_PATTERNS = [
    # Racial, ethnic, religious, and identity slurs
    r'\b(n+i+g+g+[aeiou]+r*|n+i+g+a+|c+h+i+n+k+|k+y+k+e+|g+o+o+k+|s+p+i+c+|w+e+t+b+a+c+k+)\b',
    r'\b(f+a+g+g?o?t?s?|d+y+k+e+|t+r+a+n+n+y+)\b',
    r'\b(r+e+t+a+r+d+[s]?|t+a+r+d+s?)\b',
    
    # Hate speech against groups
    r'\b(kill\s+all\s+(jews|muslims|blacks|whites|gays|trans|women|men))\b',
    r'\b(white\s+power|heil\s+hitler|nazi|gas\s+the)\b',
    
    # Real-world violent threats / self-harm
    r'\b(i(\'ll|\s+will)\s+(kill|murder|dox|stalk|bomb)\s+you(\s+in\s+real\s+life|\s+irl)?)\b',
    r'\b(kill\s+your\s*self|kms|kys|hang\s+your\s*self|slit\s+your\s*wrists)\b',
    r'\b(i\s+know\s+where\s+you\s+live|doxx?ing)\b'
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_PATTERNS]

def is_safe_line(text: str) -> tuple[bool, str]:
    """
    Checks if a chat line meets strict safety standards:
    - No slurs (racial, ethnic, religious, identity)
    - No hate speech
    - No real-world threats or self-harm
    Returns: (is_safe, reason)
    """
    if not text:
        return True, ""

    for pattern in _COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return False, f"Prohibited term detected: '{match.group(0)}'"

    return True, ""

def filter_or_sanitize(text: str, fallback_text: str = "Good play team!") -> str:
    """
    Validates text. If unsafe, returns fallback_text.
    """
    safe, _ = is_safe_line(text)
    if not safe:
        return fallback_text
    return text

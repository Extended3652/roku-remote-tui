"""Fuzzy search utilities."""
import re

def normalize_text(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def is_subsequence(query, text):
    if not query:
        return True
    qi = 0
    for ch in text:
        if qi < len(query) and ch == query[qi]:
            qi += 1
            if qi == len(query):
                return True
    return False

def fuzzy_score(query, text):
    q = normalize_text(query)
    t = normalize_text(text)
    if not q:
        return 0
    if q == t:
        return 1000
    score = 0
    if t.startswith(q):
        score += 600
    if q in t:
        score += 450
    q_tokens = q.split()
    t_tokens = t.split()
    token_hits = 0
    for tok in q_tokens:
        if tok in t_tokens:
            token_hits += 1
        elif tok in " ".join(t_tokens):
            token_hits += 0.6
    if q_tokens:
        score += int(200 * (token_hits / len(q_tokens)))
    q_compact = q.replace(" ", "")
    t_compact = t.replace(" ", "")
    if len(q_compact) <= 6 and is_subsequence(q_compact, t_compact):
        score += 220
    score -= int(abs(len(t_compact) - len(q_compact)) * 0.5)
    return max(0, score)

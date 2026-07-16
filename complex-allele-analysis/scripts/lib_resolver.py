"""
Partner-variant resolver: maps a variant identifier as written in free text
(protein like R117H, legacy nucleotide like 3791C/T, cDNA, or a common name
like F508del) to a canonical HGVS cDNA name, using a combined CFTR1 + CFTR2
alias index (see 01_build_index_and_screen.py).

Design goals:
  - Accept many notations (C/T vs C->T vs C>T; 3-letter vs 1-letter protein; *,Ter -> X).
  - Collapse notation-equivalent cDNAs (c.1521_1523del == ...delCTT; insT == dup at same pos).
  - Refuse to guess when an alias maps to genuinely different variants (e.g. c.3845G>A vs c.3846G>A).

Used by 02_resolve_and_assemble.py.
"""
import json, re, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
_INDEX_PATH = os.path.join(_HERE, "..", "intermediate", "alias_index.json")
_MUTATIONS_PATH = os.path.join(_REPO, "data", "mutations.json")

_idx = json.load(open(_INDEX_PATH))

aa3to1 = {'Ala':'A','Arg':'R','Asn':'N','Asp':'D','Cys':'C','Gln':'Q','Glu':'E','Gly':'G',
          'His':'H','Ile':'I','Leu':'L','Lys':'K','Met':'M','Phe':'F','Pro':'P','Ser':'S',
          'Thr':'T','Trp':'W','Tyr':'Y','Val':'V','Ter':'X','Sec':'U'}


def norm_key(s):
    if not s: return None
    s = str(s).strip().replace('->', '>').replace('/', '>')
    s = re.sub(r'\s+', '', s)
    s = s.replace('[delta]', '').replace('delta', '').replace('Δ', '').replace('(', '').replace(')', '')
    return s.lower()


def _three_to_one(tok):
    """Arg74Trp -> R74W; p.Gly542*/p.Arg1162Ter -> G542X/R1162X."""
    t = tok.strip()
    t = re.sub(r'^p\.?', '', t)
    m = re.match(r'^([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|\*|X|Ter|=)$', t)
    if m and m.group(1) in aa3to1:
        a1 = aa3to1[m.group(1)]; num = m.group(2); r = m.group(3)
        a2 = {'*':'X', 'Ter':'X', 'X':'X', '=':'='}.get(r, aa3to1.get(r, r))
        return a1 + num + a2
    m2 = re.match(r'^p?\.?([A-Z])(\d+)(\*|Ter)$', t)
    if m2: return m2.group(1) + m2.group(2) + 'X'
    return None


def _cands(tok):
    yield tok
    alt = tok.replace('delF508', 'F508del').replace('DeltaF508', 'F508del').replace('deltaF508', 'F508del')
    alt = re.sub(r'^d?f508$', 'F508del', alt, flags=re.I)
    if alt != tok: yield alt
    if re.match(r'^(d|delta)?F508$', tok, re.I): yield 'F508del'
    three = _three_to_one(tok)
    if three: yield three
    if '*' in tok:
        m = re.match(r'^p?\.?([A-Z])(\d+)\*$', tok)
        if m: yield m.group(1) + m.group(2) + 'X'


_cftr1_primary = set()
try:
    for _m in json.load(open(_MUTATIONS_PATH)):
        if _m.get('cdna_name'): _cftr1_primary.add(_m['cdna_name'])
except Exception:
    pass

_PLACEHOLDER = {'wild-type/reference', 'polyt/tg', 'wild-type', 'reference'}


def _valid_cdna(v):
    if not v: return False
    if '|' in v or ' ' in v: return False
    if v.lower() in _PLACEHOLDER: return False
    return v.startswith('c.') or v.startswith('g.') or v.startswith('m.') or v.startswith('n.')


def _canon(v):
    """Collapse notation variants of the SAME change (trailing bases after del/ins/dup)."""
    c = re.sub(r'(del|dup)[ACGT]+$', r'\1', v)
    c = re.sub(r'ins[ACGT]+$', 'ins', c)
    return c


def _basepos(v):
    m = re.search(r'(-?\d+)', v)
    return m.group(1) if m else None


def _pick(vals):
    good = [v for v in vals if _valid_cdna(v)]
    good = list(dict.fromkeys(good))
    if not good: return None
    if len(good) == 1: return good[0]
    if len({_canon(v) for v in good}) == 1:                 # notation-only difference
        pref = [v for v in good if v in _cftr1_primary]
        return (pref or good)[0]
    if len({_basepos(v) for v in good}) == 1:               # insT vs dup at same position
        pref = [v for v in good if v in _cftr1_primary]
        return (pref or sorted(good, key=len))[0]
    return None                                             # genuinely ambiguous


def resolve(tok):
    """Return a canonical cDNA name for a partner token, or None if unresolvable/ambiguous."""
    if not tok: return None
    for cand in _cands(tok):
        k = norm_key(cand)
        if k and k in _idx:
            r = _pick(_idx[k])
            if r: return r
    k = norm_key(re.sub(r'[^\w>+\-\*]', '', tok))
    if k and k in _idx:
        r = _pick(_idx[k])
        if r: return r
    return None

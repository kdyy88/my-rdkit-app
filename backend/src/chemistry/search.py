"""PubChem search and data retrieval utilities."""

import json
import os
import re
from functools import lru_cache
from typing import Iterable
from urllib.parse import quote
from urllib.request import urlopen

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pubchempy as pcp
    PUBCHEMPY_AVAILABLE = True
except ImportError:
    PUBCHEMPY_AVAILABLE = False


def _extract_candidate_queries(text: str) -> list[str]:
    """Extract generic candidate queries from fuzzy NL input (no molecule hardcoding)."""
    raw = text.strip()
    if not raw:
        return []

    candidates: list[str] = [raw]

    # Chinese phrase chunks (remove common grammatical glue words)
    zh_chunks = [
        c
        for c in re.split(r"[，。！？、；：,.!?;:\s并且和与对将把的地得了吧啊呀呢请帮我给出画出标出简要分析解释性质结构化]", raw)
        if c
    ]
    candidates.extend(sorted(set(zh_chunks), key=len, reverse=True))

    # Alnum / SMILES-like tokens
    token_chunks = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{1,}|[A-Za-z0-9@+\-\[\]\(\)=#/\\]{2,}", raw)
    candidates.extend(token_chunks)

    # Deduplicate while preserving order
    seen = set()
    ordered: list[str] = []
    for c in candidates:
        c = c.strip("'\"()[]{}")
        if not c or c in seen:
            continue
        seen.add(c)
        ordered.append(c)
    return ordered


def _pubchem_lookup_smiles_by_name(name: str) -> str | None:
    """Lookup canonical smiles by exact name via PubChem REST."""
    encoded = quote(name, safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/CanonicalSMILES/JSON"
    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        props = payload.get("PropertyTable", {}).get("Properties", [])
        if props:
            return props[0].get("CanonicalSMILES")
    except Exception:
        return None
    return None


def _pubchem_autocomplete(query: str) -> Iterable[str]:
    """Use PubChem autocomplete for fuzzy candidate expansion."""
    encoded = quote(query, safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{encoded}/JSON?limit=8"
    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload.get("dictionary_terms", {}).get("compound", []):
            if isinstance(item, str) and item.strip():
                yield item.strip()
    except Exception:
        return


@lru_cache(maxsize=256)
def _llm_translate_to_chemical_name(text: str) -> str | None:
    """Translate fuzzy NL molecule mention to English chemical name via LLM (optional)."""
    if not OPENAI_AVAILABLE:
        return None
    if not re.search(r"[\u4e00-\u9fff]", text):
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if base_url.endswith("/responses"):
        base_url = base_url[: -len("/responses")]

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "你是化学命名助手。将输入中的分子名称翻译/标准化为英文常用名或IUPAC名。只输出一个短字符串，不要解释。",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=24,
            temperature=0,
        )
        name = (resp.choices[0].message.content or "").strip().strip("'\"")
        return name or None
    except Exception:
        return None


@lru_cache(maxsize=512)
def name_to_smiles(compound_name: str) -> str | None:
    """
    Convert compound name to SMILES using PubChem API.
    Uses pubchempy library if available, falls back to REST API.
    
    Args:
        compound_name: Common name or IUPAC name of the compound
        
    Returns:
        SMILES string or None if not found
    """
    if not compound_name or not compound_name.strip():
        return None

    candidate_names = _extract_candidate_queries(compound_name)

    llm_guess = _llm_translate_to_chemical_name(compound_name)
    if llm_guess and llm_guess not in candidate_names:
        candidate_names.append(llm_guess)

    # Try pubchempy first (more robust)
    if PUBCHEMPY_AVAILABLE:
        for candidate in candidate_names:
            try:
                compounds = pcp.get_compounds(candidate, 'name')
                if compounds:
                    # Use the smiles property (recommended in pubchempy 2.0+)
                    return getattr(compounds[0], 'smiles', None) or compounds[0].canonical_smiles
            except Exception:
                continue  # Fall back to REST API
    
    # Fallback to PubChem REST exact-name lookup
    for candidate in candidate_names:
        smiles = _pubchem_lookup_smiles_by_name(candidate)
        if smiles:
            return smiles

    # Final fallback: fuzzy autocomplete -> exact lookup
    for candidate in candidate_names:
        for guess in _pubchem_autocomplete(candidate):
            smiles = _pubchem_lookup_smiles_by_name(guess)
            if smiles:
                return smiles

    return None


@lru_cache(maxsize=2048)
def fetch_pubchem_xlogp(smiles: str) -> float | None:
    """
    Fetch XLogP value from PubChem for a given SMILES.
    
    Args:
        smiles: SMILES string representation of a molecule
        
    Returns:
        XLogP value or None if query fails
    """
    encoded = quote(smiles, safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{encoded}/property/XLogP/JSON"
    
    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        props = payload.get("PropertyTable", {}).get("Properties", [])
        if not props:
            return None
        xlogp = props[0].get("XLogP")
        return float(xlogp) if xlogp is not None else None
    except Exception:
        return None

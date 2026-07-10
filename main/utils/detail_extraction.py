from __future__ import annotations

import re

from .base import tokenize

STREET_PATTERN = r"\b(JALAN|JL|JLN)\b\.?\s*"
BUILDING_PATTERN = r"\b(GEDUNG|GD|GDG|GED|MENARA|MNR|TOWER|TWR|WISMA|GRAHA|GRIYA|PLAZA|MALL|RUKO|RUKAN|BUILDING|OFFICE|SUITE|KOMPLEK|KOMPLEKS|PERKANTORAN|APARTEMEN|APARTMENT|CENTRE|CENTER|SENTRA|PARK|SQUARE)\b\.?"
FLOOR_PATTERN = r"\b(LANTAI|LT|LTAI|FLOOR|FLR)\b\.?\s*([A-Z0-9\-]+)"
NO_PATTERN = r"\b(NOMOR|NMR|NO)\b\.?\s*([A-Z0-9\-\/]+)"
BLOK_PATTERN = r"\bBLOK\b\.?\s*([A-Z0-9\-]+)"
KAV_PATTERN = r"\bKAV(?:LING)?\b\.?\s*([A-Z0-9\-]+)"
POSTAL_PATTERN = r"(?<!\d)(\d{5})(?!\d)"

RT_RW_PATTERNS = [
    r"\bRT\s*/?\s*RW\b\.?\s*(\d+)\s*/\s*(\d+)",
    r"\bRT\b\.?\s*(\d+)\s*/\s*RW\b\.?\s*(\d+)",
    r"\bRT\b\.?\s*(\d+)\D{0,15}RW\b\.?\s*(\d+)",
    r"\bRT\b\.?\s*(\d+)\s*/\s*(\d+)\b",
]

BUILDING_PATTERN_RE = re.compile(
    BUILDING_PATTERN +
    r"\s*([A-Z0-9][A-Z0-9\-]*(?:\s+[A-Z0-9][A-Z0-9\-]*){0,2})"
)

JALAN_PATTERN_RE = re.compile(
    STREET_PATTERN +
    r"([A-Z0-9][A-Z0-9\-]*(?:\s+[A-Z0-9][A-Z0-9\-]*){0,3})"
)

STRUKTURAL_WORDS = {
    "NO", "NOMOR", "NMR",
    "LT", "LANTAI", "LTAI", "FLOOR", "FLR",
    "RT", "RW", "BLOK", "KAV", "KAVLING",
}


def get_known_wilayah_tokens(df_prov, df_kabkota, df_kec, df_desa):
    return (
        set(tokenize(" ".join(df_prov["nama_core"])))
        | set(tokenize(" ".join(df_kabkota["nama_core"])))
        | set(tokenize(" ".join(df_kec["nama_core"])))
        | set(tokenize(" ".join(df_desa["nama_core"])))
    )


def extract_and_remove_kodepos(text):
    m = re.search(POSTAL_PATTERN, text)
    if not m:
        return None, text
    return m.group(1), text[:m.start()] + text[m.end():]


def extract_and_remove_rt_rw(text):
    for pattern in RT_RW_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return m.group(1), m.group(2), text[:m.start()] + text[m.end():]
    return None, None, text


def extract_and_remove_no(text):
    m = re.search(NO_PATTERN, text)
    if not m:
        return None, text
    return m.group(2), text[:m.start()] + text[m.end():]


def extract_and_remove_lantai(text):
    m = re.search(FLOOR_PATTERN, text)
    if not m:
        return None, text
    return m.group(2), text[:m.start()] + text[m.end():]


def extract_and_remove_blok(text):
    m = re.search(BLOK_PATTERN, text)
    if not m:
        return None, text
    return m.group(1), text[:m.start()] + text[m.end():]


def extract_and_remove_kav(text):
    m = re.search(KAV_PATTERN, text)
    if not m:
        return None, text
    return m.group(1), text[:m.start()] + text[m.end():]


def _limit_by_known_tokens(words, known_wilayah_tokens=None):
    cut_index = len(words)
    if known_wilayah_tokens:
        for i, word in enumerate(words):
            if word in known_wilayah_tokens and len(word) >= 4:
                cut_index = i
                break

    for i, word in enumerate(words[:cut_index]):
        if word in STRUKTURAL_WORDS:
            cut_index = i
            break

    return cut_index


def extract_building_name(text, known_wilayah_tokens=None):
    if text is None:
        return None

    m = BUILDING_PATTERN_RE.search(str(text).upper())
    if not m:
        return None

    words = m.group(1).split()
    cut_index = _limit_by_known_tokens(words, known_wilayah_tokens)
    nama = " ".join(words[:cut_index]).strip(" .,-")
    return nama or None


def extract_street_name(text, known_wilayah_tokens=None):
    if text is None:
        return None

    m = JALAN_PATTERN_RE.search(str(text).upper())
    if not m:
        return None

    words = m.group(1).split()
    cut_index = _limit_by_known_tokens(words, known_wilayah_tokens)

    # Nama jalan boleh dimulai dengan kata generik seperti BLOK M.
    for i, word in enumerate(words[:cut_index]):
        if i == 0:
            continue
        if word in STRUKTURAL_WORDS:
            cut_index = i
            break

    nama = " ".join(words[:cut_index]).strip(" .,-")
    return nama or None


def extract_and_remove_gedung(text, known_wilayah_tokens):
    nama = extract_building_name(text, known_wilayah_tokens=known_wilayah_tokens)
    if not nama:
        return None, text

    m = BUILDING_PATTERN_RE.search(str(text).upper())
    if not m:
        return None, text

    consumed = m.group(0)[:len(m.group(0)) - len(m.group(1))] + nama
    return nama, text.replace(consumed, "", 1)


def extract_and_remove_jalan(text, known_wilayah_tokens):
    nama = extract_street_name(text, known_wilayah_tokens=known_wilayah_tokens)
    if not nama:
        return None, text

    m = JALAN_PATTERN_RE.search(str(text).upper())
    if not m:
        return None, text

    consumed = m.group(0)[:len(m.group(0)) - len(m.group(1))] + nama
    return nama, text.replace(consumed, "", 1)


def extract_address_parts(text, known_wilayah_tokens=None):
    remaining = str(text or "").upper()

    kodepos, remaining = extract_and_remove_kodepos(remaining)
    rt, rw, remaining = extract_and_remove_rt_rw(remaining)
    no, remaining = extract_and_remove_no(remaining)
    lantai, remaining = extract_and_remove_lantai(remaining)
    gedung, remaining = extract_and_remove_gedung(remaining, known_wilayah_tokens or set())
    jalan, remaining = extract_and_remove_jalan(remaining, known_wilayah_tokens or set())
    blok, remaining = extract_and_remove_blok(remaining)
    kav, remaining = extract_and_remove_kav(remaining)

    return {
        "kodepos": kodepos,
        "rt": rt,
        "rw": rw,
        "no": no,
        "lantai": lantai,
        "gedung": gedung,
        "jalan": jalan,
        "blok": blok,
        "kav": kav,
        "remaining_text": re.sub(r"\s+", " ", remaining).strip(" ,."),
    }

import re

from .library import _ALIAS_PATTERN, _ALL_ALIASES

def tokenize(text):
    return re.findall(r"[A-Z0-9]+", str(text))

def expand_abbreviations(text):
    return _ALIAS_PATTERN.sub(lambda m: _ALL_ALIASES[m.group(1)], text)
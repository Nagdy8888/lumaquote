"""A deliberately small confirmation language independent of model interpretation."""

import re

_ITEM = r"([1-9][0-9]{0,4})\s+(?:(?:UNITS?|PCS|PIECES?)\s+(?:OF\s+)?)?([A-Z]{2}-[0-9]{3})"
_SEPARATOR = r"[ \t]*(?:,|;|\bAND\b|\r?\n)[ \t]*"
_INTRO = r"(?:(?:PLEASE\s+)?(?:QUOTE|CONFIRM|ORDER)|(?:I|WE)\s+NEED)\s+"
_FLAGS = re.IGNORECASE | re.ASCII
_REQUEST = re.compile(rf"(?:{_INTRO})?{_ITEM}(?:{_SEPARATOR}{_ITEM}){{0,19}}(?:[ \t]*[.!])?", _FLAGS)
_PAIRS = re.compile(_ITEM, _FLAGS)


def parse_written_request(body: str) -> list[tuple[str, int]] | None:
    """Return a complete explicit current order, or None when any text needs interpretation.

    Accept only an optional positive request prefix followed by 1-20 unique
    quantity/SKU pairs, separated by comma, semicolon, 'and' or newline. Counts
    are ASCII integers in 1..10000; units/pcs/pieces are optional, packs are not.
    The entire message must match, so negation, alternatives, quoted examples,
    commercial promises and injected instructions cannot be ignored as suffixes.
    Case and harmless whitespace are normalized, never uncertain product codes.
    No I/O or catalog/price/approval authority is provided. Callers must ask for
    a complete restatement when parsing fails instead of extracting substrings.
    """
    if len(body) > 16000 or not _REQUEST.fullmatch(body.strip()):
        return None
    pairs = [(sku.upper(), int(quantity)) for quantity, sku in _PAIRS.findall(body)]
    if len(pairs) > 20 or any(quantity > 10000 for _, quantity in pairs):
        return None
    if len({sku for sku, _ in pairs}) != len(pairs):
        return None
    return pairs

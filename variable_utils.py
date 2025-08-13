def extract_all_variables(text: str):
    """Extract all variables from text with their positions."""
    import re
    variables = []
    pattern = r'\[([^\]]+)\]'
    for match in re.finditer(pattern, text):
        var_name = match.group(1).strip()
        start, end = match.span()
        full_match = match.group(0)  # The full [variable] including brackets
        variables.append((var_name, start, end, full_match))
    return variables

# ---------------------------------------------------------------------------
# DOCX helpers
# ---------------------------------------------------------------------------
from typing import Iterator

def iter_paragraphs(doc) -> Iterator["Paragraph"]:
    """Yield every paragraph in *doc*, including those inside tables.

    This walks the python-docx object tree recursively so that variables inside
    table cells are not missed during extraction or replacement.
    """
    try:
        from docx.table import _Cell  # type: ignore
    except ImportError:
        raise ImportError("python-docx is required. Run: pip install python-docx")

    def _walk(parent):
        # yield direct paragraphs
        for p in parent.paragraphs:  # type: ignore[attr-defined]
            yield p
        # recurse into tables/cells
        for tbl in getattr(parent, "tables", []):
            for row in tbl.rows:
                for cell in row.cells:
                    yield from _walk(cell)
    
    yield from _walk(doc) 


def iter_all_paragraphs(doc) -> Iterator["Paragraph"]:
    """Yield paragraphs from the main document body, headers, and footers, including tables.

    This ensures replacements also occur in headers/footers where variables frequently appear
    (e.g., titles, running headers).
    """
    # Body
    yield from iter_paragraphs(doc)
    # Headers/Footers per section
    for section in getattr(doc, "sections", []):
        header = getattr(section, "header", None)
        if header is not None:
            for p in getattr(header, "paragraphs", []):
                yield p
            for tbl in getattr(header, "tables", []):
                for row in tbl.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            yield p


def iter_all_text_nodes(doc):
    """Yield all w:t elements (text nodes) from body, headers, and footers.

    This catches text inside shapes/text boxes and any nested structures because
    it queries the XML directly for all w:t nodes.
    """
    try:
        from lxml import etree  # noqa: F401
    except Exception:
        # lxml is a dependency of python-docx, so this should be available
        pass
    WNS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    # Body
    for t in doc.element.xpath('.//w:t', namespaces=WNS):
        yield t
    # Headers/Footers per section
    for section in getattr(doc, "sections", []):
        header_el = getattr(getattr(section, "header", None), "_element", None)
        if header_el is not None:
            for t in header_el.xpath('.//w:t', namespaces=WNS):
                yield t
        footer_el = getattr(getattr(section, "footer", None), "_element", None)
        if footer_el is not None:
            for t in footer_el.xpath('.//w:t', namespaces=WNS):
                yield t
        # Note: Footer paragraphs are already covered by the XPath sweep above

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

import re as _re

def normalize_variable_name(name: str) -> str:
    """Canonical normalization for variable keys.

    - strip whitespace
    - lowercase
    - remove surrounding brackets
    - collapse whitespace and punctuation to single spaces
    """
    if name is None:
        return ""
    t = str(name).strip()
    if t.startswith('[') and t.endswith(']'):
        t = t[1:-1].strip()
    t = t.lower()
    t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
    t = _re.sub(r"\s+", " ", t).strip()
    return t
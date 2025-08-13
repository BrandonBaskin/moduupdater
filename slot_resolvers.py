#!/usr/bin/env python3
"""
Slot-type resolvers for Smart Wizard suggestions.

Deterministic, evidence-based candidates from SOURCE text and local context.
Never return a suggestion that fails type validators.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Optional

from validators import validate_by_type


@dataclass
class Candidate:
    value: str
    score: float
    anchor: str
    snippet: str
    ref: str


def _window(text: str, around: str, radius: int = 240) -> str:
    if not text or not around:
        return text or ""
    low = text.lower()
    i = low.find(around.lower())
    if i == -1:
        return text[: min(len(text), 2 * radius)]
    s = max(0, i - radius)
    e = min(len(text), i + len(around) + radius)
    return text[s:e]


TTY_PATTS = [
    re.compile(r"(?i)\bTTY\b[:\s]*(711|\d{1}-\d{3}-\d{3}-\d{4})"),
    re.compile(r"(?i)TTY users call\s*(711|\d{1}-\d{3}-\d{3}-\d{4})"),
]


def tty_candidates(source_text: str, local_ctx: str) -> List[Candidate]:
    cands: List[Candidate] = []
    win = _window(source_text or "", local_ctx or "", radius=600)
    for patt in TTY_PATTS:
        for m in patt.finditer(win):
            val = m.group(1)
            score = 100 if val == "711" else 80
            snippet = win[max(0, m.start() - 60) : m.end() + 60]
            cands.append(Candidate(val=val, score=score, anchor="TTY", snippet=snippet, ref="source:win"))
    # fallback: global 711 when TTY appears somewhere
    if source_text and ("tty" in (source_text or "").lower()) and ("711" in source_text) and not any(
        c.value == "711" for c in cands
    ):
        j = source_text.find("711")
        snippet = source_text[max(0, j - 60) : j + 60]
        cands.append(Candidate("711", 60, "TTY", snippet, "source:global"))
    return sorted(cands, key=lambda c: c.score, reverse=True)


RANGE_FALL = re.compile(
    r"(?i)(Oct(?:ober)?\.?\s*1\s*[–-]\s*Mar(?:ch)?\.?\s*31).*?(\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.)\s*(?:to|–|-)\s*\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.))"
)
RANGE_SPR = re.compile(
    r"(?i)(Apr(?:il)?\.?\s*1\s*[–-]\s*Sep(?:t(?:ember)?)?\.?\s*30).*?(\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.)\s*(?:to|–|-)\s*\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.))"
)
SINGLE_HOURS = re.compile(r"(?i)Hours (?:are|:)\s*(24\s*hours,\s*7\s*days(?:\s*a\s*week)?|.+)")


def hours_candidates(source_text: str, local_ctx: str) -> List[Candidate]:
    cands: List[Candidate] = []
    win = _window(source_text or "", local_ctx or "", radius=900)
    mf = RANGE_FALL.search(win)
    ms = RANGE_SPR.search(win)
    if mf and ms:
        fall = mf.group(1).replace(".", "")
        spr = ms.group(1).replace(".", "")
        value = f"{fall}: {mf.group(2)}; {spr}: {ms.group(2)}."
        cands.append(Candidate(value, 100, "Hours", win[:120], "source:win"))
    else:
        m1 = SINGLE_HOURS.search(win)
        if m1:
            cands.append(Candidate(m1.group(1), 70, "Hours", win[:120], "source:win"))
    return cands


def dba_candidates(source_text: str, local_ctx: str, mao_name: str = "") -> List[Candidate]:
    cands: List[Candidate] = []
    win = _window(source_text or "", local_ctx or "", radius=600)
    dba_patt = re.compile(r"(?i)\b(d\/b\/a|doing business as)\b[:\s]*(.+)")
    m = dba_patt.search(win)
    if m:
        val = m.group(2).strip()
        cands.append(Candidate(val, 90, "DBA", win[:120], "source:win"))
    if mao_name:
        paren = re.compile(rf"(?i)\b{re.escape(mao_name)}\b\s*\(([^)]*?)\)")
        m2 = paren.search(win)
        if m2:
            val = m2.group(1).strip()
            cands.append(Candidate(val, 80, "DBA", win[:120], "source:win"))
    # de-dup
    seen = set(); out = []
    for c in cands:
        if c.value not in seen:
            seen.add(c.value)
            out.append(c)
    return out


def alt_formats_candidate(model_template: str) -> List[Candidate]:
    if not model_template:
        return []
    return [Candidate(model_template, 100, "model", model_template[:100], "template")]


def suggestions_for(slot_type: str, local_ctx: str, source_text: str = "", known_values: Optional[Dict[str, str]] = None, model_templates: Optional[Dict[str, str]] = None) -> List[str]:
    known_values = known_values or {}
    model_templates = model_templates or {}
    out: List[str] = []
    if slot_type == "tty_number":
        for c in tty_candidates(source_text, local_ctx):
            ok, _ = validate_by_type("tty_number", c.value)
            if ok:
                out.append(c.value)
        return list(dict.fromkeys(out))[:5]
    if slot_type == "business_hours":
        for c in hours_candidates(source_text, local_ctx):
            ok, _ = validate_by_type("business_hours", c.value)
            if ok:
                out.append(c.value)
        return list(dict.fromkeys(out))[:5]
    if slot_type == "organization":
        mao = known_values.get("MAO_name", "")
        for c in dba_candidates(source_text, local_ctx, mao_name=mao):
            ok, _ = validate_by_type("organization", c.value)
            if ok:
                out.append(c.value)
        return list(dict.fromkeys(out))[:5]
    # High-context alternate formats (template-driven)
    if "alternate format" in (local_ctx or "").lower():
        tmpl = model_templates.get("alternate_formats_2026", "")
        for c in alt_formats_candidate(tmpl):
            out.append(c.value)
        return list(dict.fromkeys(out))[:3]
    return []



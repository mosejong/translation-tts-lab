"""Vietnamese post-processing for school-notice translation outputs.

The source is ASCII-only on purpose. Vietnamese and Korean strings are written as
Unicode escapes so Windows shell encoding cannot corrupt the rules.
"""
from __future__ import annotations

import re

SCHOOL_CONTEXT_TERMS = (
    "\ud559\uad50", "\ud559\ub144", "\ud559\uc0dd", "\ucd08\ub4f1\ud559\uc0dd", "\uc804\uad50\uc0dd",
    "\ud559\ubd80\ubaa8", "\uac00\uc815\ud1b5\uc2e0\ubb38", "\ud604\uc7a5\uccb4\ud5d8\ud559\uc2b5",
    "\uccb4\ud5d8\ud559\uc2b5", "\ub4f1\uad50", "\ud558\uad50", "\ub2f4\uc784",
)
STUDENT_CONTEXT_TERMS = (
    "\ud559\uc0dd", "\ud559\ub144", "\ucd08\ub4f1\ud559\uc0dd", "\uc804\uad50\uc0dd", "\uc544\ub3d9", "\uc790\ub140",
)
HOMEROOM_CONTEXT_TERMS = (
    "\ub2f4\uc784\uc120\uc0dd\ub2d8", "\ub2f4\uc784 \uc120\uc0dd\ub2d8", "\ub2f4\uc784\uad50\uc0ac", "\ub2f4\uc784",
)
KINDERGARTEN_CONTEXT_TERMS = (
    "\uc720\uce58\uc6d0\uc0dd", "\uc720\uce58\uc6d0", "\uc6d0\uc0dd", "\uc720\uc544",
)
FIELD_TRIP_CONTEXT_TERMS = (
    "\ud604\uc7a5\uccb4\ud5d8\ud559\uc2b5", "\uccb4\ud5d8\ud559\uc2b5", "\uc18c\ud48d", "\uc218\ub828\ud68c",
)

STUDENT_PATTERNS = (
    re.compile(r"\bsinh vi(?:\u00ean|en)\b", re.IGNORECASE),
    re.compile(r"\bh(?:\u1ecd|o)c vi(?:\u00ean|en)\b", re.IGNORECASE),
)
HOMEROOM_PATTERNS = (
    re.compile(r"gi(?:\u00e1|a)o vi(?:\u00ean|en) gi(?:\u00e1|a)m (?:\u0111|d)(?:\u1ed1|o)c", re.IGNORECASE),
    re.compile(r"gi(?:\u00e1|a)o vi(?:\u00ean|en) qu(?:\u1ea3|a)n l(?:\u00fd|y)", re.IGNORECASE),
    re.compile(r"gi(?:\u00e1|a)o vi(?:\u00ean|en) ph(?:\u1ee5|u) tr(?:\u00e1|a)ch", re.IGNORECASE),
)
KINDERGARTEN_PATTERNS = (
    re.compile(r"H\u1ecdc vi\u1ec7n sinh vi\u00ean m\u1eabu gi\u00e1o", re.IGNORECASE),
    re.compile(r"Hoc vien sinh vien mau giao", re.IGNORECASE),
    re.compile(r"H\u1ecdc vi\u1ec7n m\u1eabu gi\u00e1o", re.IGNORECASE),
    re.compile(r"Hoc vien mau giao", re.IGNORECASE),
    re.compile(r"sinh vi(?:\u00ean|en) m(?:\u1eabu|au) gi(?:\u00e1|a)o", re.IGNORECASE),
)
FIELD_TRIP_PATTERNS = (
    re.compile(r"h(?:\u1ecd|o)c t(?:\u1ead|a)p th(?:\u1ef1|u)c t(?:\u1ead|a)p t(?:\u1ea1|a)i tr(?:\u01b0|u)(?:\u1edd|o)ng", re.IGNORECASE),
    re.compile(r"h(?:\u1ecd|o)c t(?:\u1ead|a)p t(?:\u1ea1|a)i tr(?:\u01b0|u)(?:\u1edd|o)ng h(?:\u1ecd|o)c", re.IGNORECASE),
)

STUDENT_TERM = "h\u1ecdc sinh"
HOMEROOM_TERM = "gi\u00e1o vi\u00ean ch\u1ee7 nhi\u1ec7m"
KINDERGARTEN_TERM = "tr\u1ebb m\u1eabu gi\u00e1o"
FIELD_TRIP_TERM = "bu\u1ed5i tr\u1ea3i nghi\u1ec7m th\u1ef1c t\u1ebf"


def apply_vi_postprocess(source_ko: str, vi_text: str) -> str:
    """Apply MVP-safe Vietnamese fixes for repeated school-domain mistranslations."""
    if not vi_text:
        return vi_text

    fixed = vi_text
    source = source_ko or ""

    if _has_any(source, STUDENT_CONTEXT_TERMS):
        for pattern in STUDENT_PATTERNS:
            fixed = pattern.sub(STUDENT_TERM, fixed)

    if _has_any(source, HOMEROOM_CONTEXT_TERMS):
        for pattern in HOMEROOM_PATTERNS:
            fixed = pattern.sub(HOMEROOM_TERM, fixed)

    if _has_any(source, KINDERGARTEN_CONTEXT_TERMS):
        for pattern in KINDERGARTEN_PATTERNS:
            fixed = pattern.sub(KINDERGARTEN_TERM, fixed)

    if _has_any(source, FIELD_TRIP_CONTEXT_TERMS):
        for pattern in FIELD_TRIP_PATTERNS:
            fixed = pattern.sub(FIELD_TRIP_TERM, fixed)

    return _normalize_spaces(fixed)


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" \n", "\n", text)
    return text.strip()

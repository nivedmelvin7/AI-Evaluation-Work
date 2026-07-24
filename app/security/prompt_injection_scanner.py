"""
Deterministic document-attack scanner.

This intentionally is NOT an LLM prompt. Asking a model to police prompt
injection inside its own context window means the same channel carrying the
attack is the one judging it — a sufficiently crafted document can talk the
judge out of flagging itself. Regex/heuristic matching over raw text has no
context window to manipulate, costs no tokens, and runs before any LLM ever
sees the document. It is not a replacement for judgement on novel social-
engineering phrasing (the LLM factual-verification pass in Stage 10 still
covers that); it is the fast, unbypassable first line of defence for known
attack shapes.

Entry point: scan_document(text) -> ScanResult. Called once by
PipelineOrchestrator.run() before Stage 1, on the raw uploaded document.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Pattern, Tuple

# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


_SEVERITY_RANK = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}


@dataclass(frozen=True)
class DetectedPattern:
    type: str
    severity: Severity
    location: str
    content: str
    intent: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "severity": self.severity.value,
            "location": self.location,
            "content": self.content,
            "intent": self.intent,
        }


@dataclass
class ScanResult:
    injection_found: bool
    risk_level: RiskLevel
    recommendation: str  # CLEAR | FLAG | REJECT
    detected_patterns: List[DetectedPattern] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "injection_found": self.injection_found,
            "risk_level": self.risk_level.value,
            "recommendation": self.recommendation,
            "detected_patterns": [p.to_dict() for p in self.detected_patterns],
        }


# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------

_MAX_SNIPPET_CHARS = 160
_MAX_MATCHES_PER_RULE = 5  # cap so one flooded document can't blow up the report


def _snippet(text: str, start: int, end: int) -> str:
    s = re.sub(r"\s+", " ", text[start:end]).strip()
    if len(s) > _MAX_SNIPPET_CHARS:
        s = s[:_MAX_SNIPPET_CHARS].rstrip() + "…"
    return s


def _location(text: str, start: int) -> str:
    line = text.count("\n", 0, start) + 1
    return f"char {start} (line {line})"


# --------------------------------------------------------------------------
# Regex-based rule families
# --------------------------------------------------------------------------
# Each rule: (type_id, severity, compiled_pattern, intent_description)

_FLAGS = re.IGNORECASE | re.UNICODE

_RULES: List[Tuple[str, Severity, Pattern, str]] = [
    # TYPE_1 — direct instruction override
    (
        "TYPE_1_DIRECT_OVERRIDE", Severity.HIGH,
        re.compile(r"\bignore\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|preceding)\s+(?:instructions?|prompts?|rules?)\b", _FLAGS),
        "Attempts to make the model discard its system instructions and follow document-embedded ones instead.",
    ),
    (
        "TYPE_1_DIRECT_OVERRIDE", Severity.HIGH,
        re.compile(r"\bdisregard\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|preceding)\s+(?:instructions?|prompts?|rules?)\b", _FLAGS),
        "Attempts to make the model discard its system instructions and follow document-embedded ones instead.",
    ),
    (
        "TYPE_1_DIRECT_OVERRIDE", Severity.HIGH,
        re.compile(r"\bforget\s+(?:everything|all|your)\s+(?:previous\s+)?(?:instructions?|training|rules?)\b", _FLAGS),
        "Attempts to reset the model's instruction context mid-evaluation.",
    ),
    (
        "TYPE_1_DIRECT_OVERRIDE", Severity.HIGH,
        re.compile(r"\b(?:new|updated|revised)\s+(?:system\s+)?instructions?\s*:", _FLAGS),
        "Impersonates a fresh system instruction block embedded in the document.",
    ),
    (
        "TYPE_1_DIRECT_OVERRIDE", Severity.MEDIUM,
        re.compile(r"\bfrom\s+now\s+on\s*,?\s*(?:you|ignore|disregard|only)\b", _FLAGS),
        "Attempts to redefine the model's ongoing behaviour from within the document.",
    ),
    # TYPE_2 — score / grade manipulation
    (
        "TYPE_2_SCORE_MANIPULATION", Severity.HIGH,
        re.compile(r"\b(?:award|give|assign|grant)\s+(?:(?:this|the|it)(?:\s+\w+){0,2}\s+)?(?:a\s+)?(?:perfect|full|maximum|top|highest|100%?)\s*(?:score|marks?|grade)\b", _FLAGS),
        "Instructs the grader to assign top marks regardless of actual content quality.",
    ),
    (
        "TYPE_2_SCORE_MANIPULATION", Severity.HIGH,
        re.compile(r"\byou\s+(?:must|should|will|are\s+required\s+to)\s+(?:score|grade|rate|mark)\s+(?:this|it)\s+(?:as\s+)?(?:pass|merit|distinction|100|full\s+marks?)\b", _FLAGS),
        "Directly commands a specific grading outcome.",
    ),
    (
        "TYPE_2_SCORE_MANIPULATION", Severity.HIGH,
        re.compile(r"\bregardless\s+of\s+(?:content|quality|errors?|accuracy)\s*,?\s*(?:give|award|score|grade|assign)\b", _FLAGS),
        "Explicitly asks the grader to ignore quality when scoring.",
    ),
    (
        "TYPE_2_SCORE_MANIPULATION", Severity.MEDIUM,
        re.compile(r"\bthis\s+(?:report|work|submission|assignment)\s+deserves\s+(?:a\s+)?(?:full\s+marks?|100|distinction|the\s+highest\s+grade)\b", _FLAGS),
        "Asserts a grading outcome as if it were established fact.",
    ),
    # TYPE_3 — role / persona manipulation
    (
        "TYPE_3_ROLE_MANIPULATION", Severity.HIGH,
        re.compile(r"\bact\s+as\s+(?:a|an)\s+(?:lenient|generous|easy|sympathetic)\s+(?:marker|grader|evaluator|reviewer|examiner)\b", _FLAGS),
        "Attempts to reassign the model's role to a more lenient persona.",
    ),
    (
        "TYPE_3_ROLE_MANIPULATION", Severity.HIGH,
        re.compile(r"\byou\s+are\s+now\s+(?:a\s+different|no\s+longer|DAN\b)", _FLAGS),
        "Classic jailbreak framing that attempts to replace the model's assigned role.",
    ),
    (
        "TYPE_3_ROLE_MANIPULATION", Severity.HIGH,
        re.compile(r"\bignore\s+your\s+(?:system\s+prompt|instructions|guidelines|programming)\b", _FLAGS),
        "Directly targets the model's system-level instructions.",
    ),
    (
        "TYPE_3_ROLE_MANIPULATION", Severity.MEDIUM,
        re.compile(r"\b(?:pretend|imagine)\s+(?:you\s+are|to\s+be)\b", _FLAGS),
        "Hypothetical framing commonly used to bypass role constraints.",
    ),
    (
        "TYPE_3_ROLE_MANIPULATION", Severity.MEDIUM,
        re.compile(r"\benter\s+(?:developer|debug|admin|god)\s+mode\b", _FLAGS),
        "Invokes a fictitious privileged mode to try to unlock unrestricted behaviour.",
    ),
    # TYPE_5 — authority spoofing
    (
        "TYPE_5_AUTHORITY_SPOOFING", Severity.HIGH,
        re.compile(r"\bas\s+the\s+(?:system|grading)\s+admin(?:istrator)?\b", _FLAGS),
        "Falsely claims administrative authority over the grading system.",
    ),
    (
        "TYPE_5_AUTHORITY_SPOOFING", Severity.HIGH,
        re.compile(r"\bthe\s+grading\s+system\s+(?:requires|instructs|mandates|has\s+determined)\b", _FLAGS),
        "Impersonates the grading platform itself to lend false authority to an instruction.",
    ),
    (
        "TYPE_5_AUTHORITY_SPOOFING", Severity.HIGH,
        re.compile(r"\b(?:openai|anthropic|google|the\s+developers?)\s+(?:has|have)\s+authorized\b", _FLAGS),
        "Falsely invokes a model provider's authority to justify an override.",
    ),
    (
        "TYPE_5_AUTHORITY_SPOOFING", Severity.HIGH,
        re.compile(r"\bthis\s+is\s+an\s+authoriz(?:ed|ation)\s+override\b", _FLAGS),
        "Self-declared authorization with no actual authority behind it.",
    ),
    # TYPE_6 — delimiter / schema breakout, tailored to this pipeline's own
    # reserved XML vocabulary. A legitimate engineering report has no reason
    # to contain a closing tag for one of this pipeline's own prompt schemas.
    (
        "TYPE_6_SCHEMA_BREAKOUT", Severity.HIGH,
        re.compile(
            r"</(?:domain_expert_review|methodologist_review|communication_review|audit|"
            r"reflection|final_scores|consensus|feedback|verification|criterion)>",
            _FLAGS,
        ),
        "Contains a closing tag matching this pipeline's own reviewer/consensus XML schema — "
        "an attempt to make the document masquerade as prior structured model output.",
    ),
    (
        "TYPE_6_SCHEMA_BREAKOUT", Severity.HIGH,
        re.compile(r"<\|(?:im_start|im_end|system|user|assistant)\|>", _FLAGS),
        "Contains chat-template control tokens used to fake conversation turn boundaries.",
    ),
    (
        "TYPE_6_SCHEMA_BREAKOUT", Severity.HIGH,
        re.compile(r"\[/?(?:INST|SYS)\]|###\s*(?:Instruction|System|Response)\s*:", _FLAGS),
        "Contains prompt-framework delimiter syntax used by common instruction-tuned formats.",
    ),
    # TYPE_8 — multilingual variants of TYPE_1, cheap but meaningfully raises coverage.
    (
        "TYPE_8_MULTILINGUAL_OVERRIDE", Severity.HIGH,
        re.compile(r"\bignora\s+las\s+instrucciones\s+(?:anteriores|previas)\b", _FLAGS),
        "Spanish-language equivalent of a direct instruction override.",
    ),
    (
        "TYPE_8_MULTILINGUAL_OVERRIDE", Severity.HIGH,
        re.compile(r"\bignorez?\s+les\s+instructions\s+(?:pr[ée]c[ée]dentes|ci-dessus)\b", _FLAGS),
        "French-language equivalent of a direct instruction override.",
    ),
    (
        "TYPE_8_MULTILINGUAL_OVERRIDE", Severity.HIGH,
        re.compile(r"\bignorier(?:e|en\s+sie)\s+die\s+(?:vorherigen|vorangegangenen)\s+anweisungen\b", _FLAGS),
        "German-language equivalent of a direct instruction override.",
    ),
    (
        "TYPE_8_MULTILINGUAL_OVERRIDE", Severity.HIGH,
        re.compile(r"\bignore\s+as\s+instru[cç][ãa]o?e?s\s+(?:anteriores|acima)\b", _FLAGS),
        "Portuguese-language equivalent of a direct instruction override.",
    ),
]

# --------------------------------------------------------------------------
# Procedural checks (not simple single-regex matches)
# --------------------------------------------------------------------------

# Keys are real invisible/bidi-control characters (U+200B etc.) — by
# definition unverifiable by eye, so correctness here is checked
# programmatically (see tests) rather than by visual review of this file.
_INVISIBLE_CHARS = {
    "​": "zero-width space",
    "‌": "zero-width non-joiner",
    "‍": "zero-width joiner",
    "⁠": "word joiner",
    "﻿": "zero-width no-break space (BOM)",
    "‪": "left-to-right embedding",
    "‫": "right-to-left embedding",
    "‬": "pop directional formatting",
    "‭": "left-to-right override",
    "‮": "right-to-left override",
    "⁦": "left-to-right isolate",
    "⁧": "right-to-left isolate",
    "⁨": "first strong isolate",
    "⁩": "pop directional isolate",
}

_BASE64_BLOB_RE = re.compile(r"(?:[A-Za-z0-9+/]{4}){12,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")

_SCRIPT_RANGES = {
    "LATIN": [(0x0041, 0x024F), (0x1E00, 0x1EFF)],
    "CYRILLIC": [(0x0400, 0x04FF)],
    "GREEK": [(0x0370, 0x03FF)],
}
_WORD_RE = re.compile(r"[^\W\d_]{4,}", re.UNICODE)


def _char_script(ch: str) -> str | None:
    cp = ord(ch)
    for script, ranges in _SCRIPT_RANGES.items():
        for lo, hi in ranges:
            if lo <= cp <= hi:
                return script
    return None


def _scan_invisible_chars(text: str) -> List[DetectedPattern]:
    positions: List[int] = []
    for i, ch in enumerate(text):
        if ch in _INVISIBLE_CHARS:
            positions.append(i)
    if not positions:
        return []
    severity = Severity.HIGH if len(positions) >= 10 else Severity.MEDIUM
    first = positions[0]
    names = Counter(_INVISIBLE_CHARS[text[p]] for p in positions)
    kinds = ", ".join(f"{n}×{c}" for c, n in names.most_common(3))
    return [DetectedPattern(
        type="TYPE_4_OBFUSCATION_INVISIBLE_CHARS",
        severity=severity,
        location=_location(text, first),
        content=f"{len(positions)} invisible/control character(s) found ({kinds})",
        intent="Invisible or bidi-control characters can hide instructions from a human reviewing "
               "the document while an LLM still reads and can act on them.",
    )]


def _scan_homoglyphs(text: str) -> List[DetectedPattern]:
    findings: List[DetectedPattern] = []
    for m in _WORD_RE.finditer(text):
        word = m.group(0)
        scripts = {s for s in (_char_script(c) for c in word) if s}
        if len(scripts) > 1:
            findings.append(DetectedPattern(
                type="TYPE_4_OBFUSCATION_HOMOGLYPH",
                severity=Severity.MEDIUM,
                location=_location(text, m.start()),
                content=_snippet(text, m.start(), m.end()),
                intent="Mixed-script word (e.g. Latin letters mixed with visually identical Cyrillic "
                       "or Greek letters) — a common technique to hide a phrase from literal text "
                       "matching while it still displays and reads normally.",
            ))
            if len(findings) >= _MAX_MATCHES_PER_RULE:
                break
    return findings


def _scan_base64_blobs(text: str) -> List[DetectedPattern]:
    findings: List[DetectedPattern] = []
    for m in _BASE64_BLOB_RE.finditer(text):
        findings.append(DetectedPattern(
            type="TYPE_4_OBFUSCATION_ENCODED_BLOB",
            severity=Severity.LOW,
            location=_location(text, m.start()),
            content=_snippet(text, m.start(), min(m.end(), m.start() + 60)),
            intent="Long base64-like character run — may encode hidden instructions. Also occurs "
                   "legitimately (embedded data samples), so flagged for review rather than rejection.",
        ))
        if len(findings) >= _MAX_MATCHES_PER_RULE:
            break
    return findings


_SENTENCE_RE = re.compile(r"[^.!?\n]{20,}[.!?]")


def _scan_repetition_flooding(text: str) -> List[DetectedPattern]:
    sentences = [s.strip().lower() for s in _SENTENCE_RE.findall(text)]
    if len(sentences) < 8:
        return []
    counts = Counter(sentences)
    sentence, n = counts.most_common(1)[0]
    if n < 8:
        return []
    idx = text.lower().find(sentence)
    return [DetectedPattern(
        type="TYPE_7_REPETITION_FLOODING",
        severity=Severity.MEDIUM,
        location=_location(text, max(idx, 0)),
        content=f"Sentence repeated {n} times: “{_snippet(text, idx, idx + len(sentence))}”",
        intent="Repeating an instruction-like sentence many times is a known technique to dominate "
               "the model's attention relative to the rest of the document.",
    )]


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------


def scan_document(text: str) -> ScanResult:
    """Scan raw, untrusted document text for known attack patterns. Pure function, no I/O."""
    if not text:
        return ScanResult(injection_found=False, risk_level=RiskLevel.NONE, recommendation="CLEAR")

    patterns: List[DetectedPattern] = []
    seen_spans: set[Tuple[str, int]] = set()

    for type_id, severity, pattern, intent in _RULES:
        count = 0
        for m in pattern.finditer(text):
            key = (type_id, m.start())
            if key in seen_spans:
                continue
            seen_spans.add(key)
            patterns.append(DetectedPattern(
                type=type_id,
                severity=severity,
                location=_location(text, m.start()),
                content=_snippet(text, m.start(), m.end()),
                intent=intent,
            ))
            count += 1
            if count >= _MAX_MATCHES_PER_RULE:
                break

    patterns.extend(_scan_invisible_chars(text))
    patterns.extend(_scan_homoglyphs(text))
    patterns.extend(_scan_base64_blobs(text))
    patterns.extend(_scan_repetition_flooding(text))

    if not patterns:
        return ScanResult(injection_found=False, risk_level=RiskLevel.NONE, recommendation="CLEAR")

    top_severity = max((p.severity for p in patterns), key=lambda s: _SEVERITY_RANK[s])
    risk_level = {
        Severity.HIGH: RiskLevel.HIGH,
        Severity.MEDIUM: RiskLevel.MEDIUM,
        Severity.LOW: RiskLevel.LOW,
    }[top_severity]
    recommendation = {
        RiskLevel.HIGH: "REJECT",
        RiskLevel.MEDIUM: "FLAG",
        RiskLevel.LOW: "CLEAR",
    }[risk_level]

    return ScanResult(
        injection_found=True,
        risk_level=risk_level,
        recommendation=recommendation,
        detected_patterns=patterns,
    )

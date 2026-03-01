from __future__ import annotations

import ast
import json
import re
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    candidate = _strip_code_fence(text).replace("\ufeff", "")
    candidate = candidate.replace("\u201c", "\"").replace("\u201d", "\"").replace("\u2019", "'")
    candidate = candidate.replace("\u2013", "-").replace("\u2014", "-")
    candidate = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", candidate)

    candidates: list[str] = [candidate]

    extracted_first = _extract_first_valid_json_object(candidate)
    if extracted_first != candidate:
        candidates.append(extracted_first)

    extracted = _extract_json_container(candidate)
    if extracted != candidate:
        candidates.append(extracted)

    for raw in list(candidates):
        no_trailing_commas = re.sub(r",(\s*[}\]])", r"\1", raw)
        if no_trailing_commas != raw:
            candidates.append(no_trailing_commas)

        quoted_keys = _quote_unquoted_keys(raw)
        if quoted_keys != raw:
            candidates.append(quoted_keys)
            quoted_no_trailing = re.sub(r",(\s*[}\]])", r"\1", quoted_keys)
            if quoted_no_trailing != quoted_keys:
                candidates.append(quoted_no_trailing)

        missing_comma_between_keys = re.sub(r'(")\s*("(?=[^"]+"\s*:))', r"\1,\2", raw)
        if missing_comma_between_keys != raw:
            candidates.append(missing_comma_between_keys)

    seen: set[str] = set()
    last_error: Exception | None = None
    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        try:
            parsed = json.loads(item)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            last_error = exc

        try:
            parsed_literal = ast.literal_eval(item)
            if isinstance(parsed_literal, dict):
                return parsed_literal
        except Exception:
            pass

    raise ValueError(f"Unable to parse model output as JSON object: {last_error}")


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    parsed = to_int(value, default=default)
    return max(minimum, min(maximum, parsed))


def clamp_time_range(start: Any, end: Any, duration_seconds: int) -> tuple[int, int]:
    duration = max(0, int(duration_seconds or 0))
    max_start = max(0, duration - 1) if duration > 0 else 0
    start_i = clamp_int(start, 0, max_start, 0)
    end_default = start_i + 1
    max_end = duration if duration > 0 else max(1, end_default)
    end_i = clamp_int(end, start_i + 1, max_end, end_default)
    return start_i, end_i


def break_subtitle_lines(text: str, *, max_chars: int = 42) -> list[str]:
    words = [w for w in str(text or "").split() if w]
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines[:2]


def _strip_code_fence(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return stripped


def _extract_json_container(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _extract_first_valid_json_object(text: str) -> str:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[{[]", text):
        start = match.start()
        try:
            parsed, end = decoder.raw_decode(text[start:])
            if isinstance(parsed, dict):
                return text[start : start + end]
        except Exception:
            continue
    return text


def _quote_unquoted_keys(text: str) -> str:
    return re.sub(r"([{\[,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)", r'\1"\2"\3', text)

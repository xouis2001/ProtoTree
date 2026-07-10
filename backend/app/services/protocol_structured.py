from typing import Any

from app.schemas.structured import StructuredProtocol
from app.services.html_sanitizer import sanitize_rich_text_html


def normalize_structured_protocol(structured: StructuredProtocol | dict[str, Any] | None) -> dict[str, Any]:
    if structured is None:
        model = StructuredProtocol()
    elif isinstance(structured, StructuredProtocol):
        model = structured
    else:
        model = StructuredProtocol.model_validate(structured)

    data = model.model_dump(mode="json")
    experiment_category = (data.get("experiment_category") or data.get("experiment_type") or "").strip()
    tags = _clean_list(data.get("tags"))
    tag_groups = _clean_list(data.get("tag_groups"))
    content_format = data.get("content_format") if data.get("content_format") in {"plain", "html"} else "plain"
    content = data.get("content") if isinstance(data.get("content"), str) else ""
    if content_format == "html":
        content = sanitize_rich_text_html(content)

    data["experiment_category"] = experiment_category
    data["experiment_type"] = experiment_category
    data["tag_groups"] = tag_groups
    data["tags"] = tags
    data["experiment_subtype"] = (data.get("experiment_subtype") or (tags[0] if tags else "") or "").strip()
    data["content"] = content
    data["content_format"] = content_format
    data["steps"] = _clean_steps(data.get("steps"))
    return data


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _clean_steps(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    steps: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        parameters = item.get("parameters") if isinstance(item.get("parameters"), dict) else {}
        steps.append(
            {
                "order": int(item.get("order") or index),
                "title": str(item.get("title") or "").strip(),
                "content": str(item.get("content") or "").strip(),
                "parameters": {str(key): str(val) for key, val in parameters.items()},
            }
        )
    return steps

from difflib import ndiff
from typing import Any

from app.models.protocol import Protocol
from app.schemas.protocol import ProtocolDiffEntry, ProtocolDiffResponse


def diff_protocols(source: Protocol, target: Protocol) -> ProtocolDiffResponse:
    changes: list[ProtocolDiffEntry] = []
    _compare_value(changes, "metadata", "title", source.title, target.title)
    _compare_value(changes, "metadata", "abstract", source.abstract, target.abstract)
    _compare_value(changes, "metadata", "version_label", source.version_label, target.version_label)
    _compare_structured(changes, source.structured or {}, target.structured or {})
    _compare_raw_text(changes, source.raw_text or "", target.raw_text or "")
    summary = {
        "added": sum(1 for change in changes if change.change_type == "added"),
        "removed": sum(1 for change in changes if change.change_type == "removed"),
        "modified": sum(1 for change in changes if change.change_type == "modified"),
        "unchanged": 0,
        "total": len(changes),
    }
    return ProtocolDiffResponse(
        source_id=source.id,
        target_id=target.id,
        source_title=source.title,
        target_title=target.title,
        summary=summary,
        changes=changes,
    )


def _compare_structured(changes: list[ProtocolDiffEntry], source: dict[str, Any], target: dict[str, Any]) -> None:
    _compare_value(changes, "structured", "experiment_name", source.get("experiment_name"), target.get("experiment_name"))
    _compare_value(changes, "structured", "experiment_type", source.get("experiment_type"), target.get("experiment_type"))
    _compare_items(changes, "steps", source.get("steps") or [], target.get("steps") or [], _step_identity)


def _compare_items(
    changes: list[ProtocolDiffEntry],
    section: str,
    source_items: list[Any],
    target_items: list[Any],
    identity_func,
) -> None:
    source_map = {identity_func(item, index): item for index, item in enumerate(source_items)}
    target_map = {identity_func(item, index): item for index, item in enumerate(target_items)}
    for key in sorted(source_map.keys() - target_map.keys(), key=str):
        changes.append(ProtocolDiffEntry(section=section, path=str(key), change_type="removed", before=source_map[key], after=None))
    for key in sorted(target_map.keys() - source_map.keys(), key=str):
        changes.append(ProtocolDiffEntry(section=section, path=str(key), change_type="added", before=None, after=target_map[key]))
    for key in sorted(source_map.keys() & target_map.keys(), key=str):
        before = source_map[key]
        after = target_map[key]
        if _normalize(before) != _normalize(after):
            changes.append(ProtocolDiffEntry(section=section, path=str(key), change_type="modified", before=before, after=after))


def _compare_raw_text(changes: list[ProtocolDiffEntry], source: str, target: str) -> None:
    if source == target:
        return
    diff_lines = [line for line in ndiff(source.splitlines(), target.splitlines()) if line.startswith("- ") or line.startswith("+ ")]
    changes.append(
        ProtocolDiffEntry(
            section="raw_text",
            path="raw_text",
            change_type="modified",
            before=source,
            after=target,
        )
    )
    for index, line in enumerate(diff_lines[:20], start=1):
        changes.append(
            ProtocolDiffEntry(
                section="raw_text_lines",
                path=f"line_change_{index}",
                change_type="removed" if line.startswith("- ") else "added",
                before=line[2:] if line.startswith("- ") else None,
                after=line[2:] if line.startswith("+ ") else None,
            )
        )


def _compare_value(changes: list[ProtocolDiffEntry], section: str, path: str, before: Any, after: Any) -> None:
    if _normalize(before) == _normalize(after):
        return
    change_type = "modified"
    if _is_empty(before) and not _is_empty(after):
        change_type = "added"
    elif not _is_empty(before) and _is_empty(after):
        change_type = "removed"
    changes.append(ProtocolDiffEntry(section=section, path=path, change_type=change_type, before=before, after=after))


def _item_identity(item: Any, index: int) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("title") or item.get("id") or f"item_{index + 1}")
    return f"item_{index + 1}"


def _step_identity(item: Any, index: int) -> str:
    if isinstance(item, dict):
        return str(item.get("order") or item.get("title") or item.get("content") or f"step_{index + 1}")
    return f"step_{index + 1}"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}

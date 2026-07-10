from html import escape
from html.parser import HTMLParser


ALLOWED_TAGS = {
    "b",
    "strong",
    "i",
    "em",
    "u",
    "p",
    "br",
    "div",
    "span",
    "font",
    "ul",
    "ol",
    "li",
    "table",
    "tbody",
    "thead",
    "tr",
    "td",
    "th",
    "pre",
    "code",
    "h2",
    "h3",
    "h4",
    "h5",
}
ALLOWED_STYLES = {"color", "text-align", "font-weight", "font-style", "text-decoration"}
VOID_TAGS = {"br"}


class _RichTextSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return
        safe_attrs = self._sanitize_attrs(tag, attrs)
        attr_text = "".join(f' {name}="{escape(value, quote=True)}"' for name, value in safe_attrs)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def _sanitize_attrs(self, tag: str, attrs: list[tuple[str, str | None]]) -> list[tuple[str, str]]:
        safe_attrs: list[tuple[str, str]] = []
        for name, value in attrs:
            if value is None:
                continue
            name = name.lower()
            if name == "style":
                style = _sanitize_style(value)
                if style:
                    safe_attrs.append((name, style))
            elif tag == "font" and name == "color" and _is_safe_color(value):
                safe_attrs.append((name, value.strip()))
        return safe_attrs


def sanitize_rich_text_html(value: str) -> str:
    parser = _RichTextSanitizer()
    parser.feed(value or "")
    parser.close()
    return "".join(parser.parts)


def _sanitize_style(value: str) -> str:
    safe_rules: list[str] = []
    for item in value.split(";"):
        if ":" not in item:
            continue
        name, raw_value = item.split(":", 1)
        name = name.strip().lower()
        css_value = raw_value.strip()
        if name not in ALLOWED_STYLES:
            continue
        if "url(" in css_value.lower() or "expression(" in css_value.lower():
            continue
        if name == "color" and not _is_safe_color(css_value):
            continue
        safe_rules.append(f"{name}: {css_value}")
    return "; ".join(safe_rules)


def _is_safe_color(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    lowered = value.lower()
    if "url(" in lowered or "expression(" in lowered or ";" in value:
        return False
    return lowered.startswith("#") or lowered.isalpha() or lowered.startswith(("rgb(", "rgba("))

"""Avatar catalog and single-image renderer API.

The renderer intentionally mirrors lulab.top homepage's top-right avatar logic
(public/index.html renderAvatarConfig): it reads the 1080px preview SVG layers from
/avatar-assets/preview/* and returns one finished circular SVG for ProtoTree <img> tags.
"""
from functools import lru_cache
import hashlib, json, re
from urllib.parse import quote
from urllib.request import Request, urlopen
from fastapi import APIRouter, Query, Response

router = APIRouter(prefix="/avatar", tags=["avatar"])
CATEGORY_ORDER = ["face", "hair", "eyes", "eyebrows", "nose", "mouth", "beard", "glasses", "accessories", "details"]
# Same order as lulab.top public/index.html renderAvatarConfig.
RENDER_ORDER = ["face", "beard", "mouth", "nose", "eyes", "eyebrows", "glasses", "hair", "accessories", "details"]
DEFAULT_COUNTS = {"face": 12, "nose": 12, "mouth": 12, "eyes": 12, "eyebrows": 12, "glasses": 12, "hair": 24, "accessories": 12, "details": 12, "beard": 12}
DEFAULT_COLORS = ["#111827", "#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a", "#0891b2", "#4f46e5"]
DEFAULT_BACKGROUNDS = ["#f4dcc8", "#dfe5d2", "#dbeafe", "#fce7f3", "#ede9fe", "#dcfce7"]
SAFE_CAT = re.compile(r"^[a-z0-9_-]+$")
SAFE_COLOR = re.compile(r"^#[0-9a-fA-F]{3,8}$")
SVG_INNER_RE = re.compile(r"<svg[^>]*>([\s\S]*?)</svg>", re.I)
FILL_STROKE_RE = re.compile(r'(fill|stroke)="(#[0-9a-fA-F]{3,8}|black|white|currentColor)"')


def _seeded_index(seed: str, salt: int, count: int) -> int:
    digest = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % count


def _random_config(seed_text: str) -> dict:
    seed = str(seed_text or "ProtoTree user").strip()
    # Homepage renderer ignores idx<=0, so generated fallback must be 1..count.
    sel = {part: f"{part}-{_seeded_index(seed, i + 1, DEFAULT_COUNTS.get(part, 1)) + 1}" for i, part in enumerate(RENDER_ORDER)}
    colors = {part: DEFAULT_COLORS[_seeded_index(seed, i + 21, len(DEFAULT_COLORS))] for i, part in enumerate(RENDER_ORDER)}
    return {"version": 1, "bg": DEFAULT_BACKGROUNDS[_seeded_index(seed, 99, len(DEFAULT_BACKGROUNDS))], "sel": sel, "colors": colors}


def _clean_config(config_text: str | None, seed: str) -> dict:
    if not config_text:
        return _random_config(seed)
    try:
        data = json.loads(config_text)
        if isinstance(data, dict) and isinstance(data.get("sel"), dict):
            return data
    except Exception:
        pass
    return _random_config(seed)


def _item_index(name: object) -> int:
    m = re.search(r"(\d+)$", str(name or ""))
    return int(m.group(1)) if m else -1


def _inner_svg(svg_text: str) -> str:
    m = SVG_INNER_RE.search(svg_text or "")
    return m.group(1) if m else (svg_text or "")


def _safe_color(color: object, fallback: str = "#000000") -> str:
    s = str(color or "").strip()
    return s if SAFE_COLOR.match(s) else fallback


def _colorize(svg_text: str, color: str) -> str:
    # Exact behavior copied from homepage: recolor fill/stroke; if no color attrs,
    # add fill to paths. This preserves the avatar-builder preview SVG geometry.
    s = FILL_STROKE_RE.sub(lambda m: f'{m.group(1)}="{color}"', svg_text or "")
    if not re.search(r'(fill|stroke)="#', s):
        s = s.replace("<path ", f'<path fill="{color}" ')
    return s


@lru_cache(maxsize=2048)
def _fetch_preview_inner(cat: str, idx: int) -> str | None:
    if cat not in DEFAULT_COUNTS or not SAFE_CAT.match(cat) or idx <= 0 or idx > max(DEFAULT_COUNTS.get(cat, 1), 64):
        return None
    url = f"https://lulab.top/avatar-assets/preview/{quote(cat)}/{idx}.svg"
    try:
        req = Request(url, headers={"User-Agent": "ProtoTree-avatar-homepage-renderer/1.0"})
        with urlopen(req, timeout=4) as r:
            if r.status != 200:
                return None
            raw = r.read(600000).decode("utf-8", "replace")
        return _inner_svg(raw)
    except Exception:
        return None


@router.get("/render.svg")
async def render_avatar(config: str | None = Query(default=None), seed: str = Query(default="ProtoTree user")):
    cfg = _clean_config(config, seed)
    sel = cfg.get("sel") or {}
    colors = cfg.get("colors") or {}
    bg = _safe_color(cfg.get("bg"), "#ffffff")
    groups: list[str] = []
    for cat in RENDER_ORDER:
        idx = _item_index(sel.get(cat))
        if idx <= 0:
            continue
        inner = _fetch_preview_inner(cat, idx)
        if not inner:
            continue
        colored = _colorize(inner, _safe_color(colors.get(cat), "#000000"))
        face_fill = ' fill="#ffffff"' if cat == "face" else ""
        groups.append(f"<g{face_fill}>{colored}</g>")
    if not groups:
        fallback = _random_config(seed)
        return await render_avatar(json.dumps(fallback, ensure_ascii=False), seed)
    svg = (
        '<svg viewBox="0 0 1080 1080" xmlns="http://www.w3.org/2000/svg" aria-label="用户头像" '
        'width="1080" height="1080" style="width:100%;height:100%;display:block;border-radius:50%;overflow:hidden;">'
        '<defs><clipPath id="avatarCircleClip"><circle cx="540" cy="540" r="540"></circle></clipPath></defs>'
        f'<rect width="1080" height="1080" rx="540" ry="540" fill="{bg}"></rect>'
        f'<g clip-path="url(#avatarCircleClip)">{"".join(groups)}</g></svg>'
    )
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})

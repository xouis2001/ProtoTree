from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.protocol import Protocol, ProtocolSource, ProtocolVisibility
from app.models.user import User, UserRole
from app.services.protocol_structured import normalize_structured_protocol
from app.services.taxonomy import seed_taxonomy


DEFAULT_AUTHOR_EMAIL = "protocol-book@prototree.org"
DEFAULT_AUTHOR_NAME = "Protocol Book"


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Protocol JSON must be a list")
    return data


def payload_from_record(record: dict[str, Any], version_label: str) -> dict[str, Any]:
    payload = record.get("import_payload_preview") if isinstance(record.get("import_payload_preview"), dict) else record
    title = str(payload.get("title") or record.get("title") or "").strip()
    raw_text = str(payload.get("raw_text") or record.get("raw_text") or "").strip()
    structured = payload.get("structured") or record.get("structured") or {}
    if not title:
        raise ValueError("Protocol record is missing title")
    if not raw_text:
        raise ValueError(f"Protocol record {title!r} is missing raw_text")
    return {
        "title": title,
        "abstract": "",
        "raw_text": raw_text,
        "structured": normalize_structured_protocol(structured),
        "version_label": version_label,
    }


async def get_or_create_author(session, email: str, commit: bool) -> User:
    result = await session.execute(select(User).where(User.email == email))
    author = result.scalar_one_or_none()
    if author is not None:
        return author

    if email == DEFAULT_AUTHOR_EMAIL:
        author = User(
            name=DEFAULT_AUTHOR_NAME,
            email=DEFAULT_AUTHOR_EMAIL,
            password_hash=get_password_hash("protocol-book-seed-disabled"),
            role=UserRole.student,
            avatar="#0f766e|1111100110011111",
            is_admin=False,
        )
        if commit:
            session.add(author)
            await session.flush()
        else:
            author.id = -1
        return author

    raise ValueError(f"Author user not found: {email}")


async def import_records(args: argparse.Namespace) -> dict[str, Any]:
    records = load_records(Path(args.input).resolve())
    payloads = [payload_from_record(record, args.version_label) for record in records]
    commit = bool(args.commit)
    stats = {"create": 0, "update": 0, "skip": 0, "errors": 0}
    details: list[dict[str, str]] = []

    try:
        async with AsyncSessionLocal() as session:
            if not args.skip_taxonomy_seed and commit:
                await seed_taxonomy(session)
            author = await get_or_create_author(session, args.author_email, commit)

            for payload in payloads:
                try:
                    existing = await session.scalar(
                        select(Protocol).where(
                            Protocol.source == ProtocolSource.base,
                            Protocol.title == payload["title"],
                            Protocol.version_label == args.version_label,
                        )
                    )
                    if existing is None:
                        stats["create"] += 1
                        details.append({"action": "create", "title": payload["title"]})
                        if commit:
                            protocol = Protocol(
                                title=payload["title"],
                                abstract=payload["abstract"],
                                visibility=ProtocolVisibility.public,
                                raw_text=payload["raw_text"],
                                structured=payload["structured"],
                                version_label=args.version_label,
                                folder_id=None,
                                source=ProtocolSource.base,
                                author_id=author.id,
                            )
                            session.add(protocol)
                            await session.flush()
                            protocol.root_id = protocol.id
                    elif args.replace_existing:
                        stats["update"] += 1
                        details.append({"action": "update", "title": payload["title"]})
                        if commit:
                            existing.abstract = payload["abstract"]
                            existing.visibility = ProtocolVisibility.public
                            existing.raw_text = payload["raw_text"]
                            existing.structured = payload["structured"]
                            existing.folder_id = None
                            existing.source = ProtocolSource.base
                            existing.author_id = author.id
                            if existing.root_id is None:
                                existing.root_id = existing.id
                            session.add(existing)
                    else:
                        stats["skip"] += 1
                        details.append({"action": "skip", "title": payload["title"]})
                except Exception as exc:
                    stats["errors"] += 1
                    details.append({"action": "error", "title": payload.get("title", "<untitled>"), "error": f"{exc.__class__.__name__}: {exc}"})

            if stats["errors"]:
                await session.rollback()
            elif commit:
                await session.commit()
            else:
                await session.rollback()
    except OperationalError as exc:
        if commit or "no such table" not in str(exc).lower():
            raise
        stats["create"] = len(payloads)
        details = [{"action": "create", "title": payload["title"]} for payload in payloads]
        return {
            "mode": "dry-run",
            "input": str(Path(args.input).resolve()),
            "author_email": args.author_email,
            "version_label": args.version_label,
            "replace_existing": bool(args.replace_existing),
            "database_status": "uninitialized",
            "note": "Database tables are missing; dry-run validated input and assumes every record would be created after migrations/init_db.",
            "stats": stats,
            "details": details,
        }

    return {
        "mode": "commit" if commit else "dry-run",
        "input": str(Path(args.input).resolve()),
        "author_email": args.author_email,
        "version_label": args.version_label,
        "replace_existing": bool(args.replace_existing),
        "stats": stats,
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Idempotently import standardized Protocol Book records as base protocols.")
    parser.add_argument("--input", default=r"backend\generated\protocol_book_v2_protocols.json")
    parser.add_argument("--author-email", default=DEFAULT_AUTHOR_EMAIL)
    parser.add_argument("--version-label", default="v2.0")
    parser.add_argument("--dry-run", action="store_true", help="Compatibility flag; dry-run is the default unless --commit is passed.")
    parser.add_argument("--commit", action="store_true", help="Write changes to the configured database.")
    parser.add_argument("--replace-existing", action="store_true", help="Update existing base protocols with the same title and version label.")
    parser.add_argument("--skip-taxonomy-seed", action="store_true", help="Do not seed taxonomy before committing.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = asyncio.run(import_records(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["stats"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

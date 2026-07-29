import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.email_outbox import EmailOutbox
from app.services.mailer import send_templated_email

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


async def _claim_one() -> dict | None:
    """Claim one due row in a short transaction; SMTP never runs in it."""
    now = _now()
    stale = now - timedelta(seconds=settings.email_outbox_lease_seconds)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EmailOutbox)
            .where(
                EmailOutbox.attempt_count < settings.email_outbox_max_attempts,
                or_(
                    (EmailOutbox.status.in_(("pending", "failed")))
                    & or_(EmailOutbox.next_attempt_at.is_(None), EmailOutbox.next_attempt_at <= now),
                    (EmailOutbox.status == "processing") & (EmailOutbox.updated_at < stale),
                ),
            )
            .order_by(EmailOutbox.created_at, EmailOutbox.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = "processing"
        row.attempt_count += 1
        row.last_error = None
        row.next_attempt_at = None
        claimed = {"id": row.id, "recipient": row.recipient, "template": row.template, "payload": row.payload}
        await session.commit()
        return claimed


async def _finish(message_id: int, error: Exception | None) -> None:
    async with AsyncSessionLocal() as session:
        row = await session.get(EmailOutbox, message_id, with_for_update=True)
        if row is None or row.status != "processing":
            return
        if error is None:
            row.status = "sent"
            row.sent_at = _now()
            row.last_error = None
            row.next_attempt_at = None
        else:
            row.status = "failed"
            row.last_error = f"{type(error).__name__}: {error}"[:4000]
            delay = min(
                settings.email_outbox_max_backoff_seconds,
                settings.email_outbox_base_backoff_seconds * (2 ** max(0, row.attempt_count - 1)),
            )
            row.next_attempt_at = _now() + timedelta(seconds=delay)
        await session.commit()


async def process_one() -> bool:
    message = await _claim_one()
    if message is None:
        return False
    error = None
    try:
        await asyncio.to_thread(
            send_templated_email, message["recipient"], message["template"], message["payload"]
        )
    except Exception as exc:  # persisted for retry; do not stop the worker
        error = exc
        logger.warning("email outbox delivery failed id=%s type=%s", message["id"], type(exc).__name__)
    await _finish(message["id"], error)
    return True


async def run_email_outbox_worker(stop: asyncio.Event) -> None:
    logger.info("email outbox worker started")
    while not stop.is_set():
        try:
            worked = await process_one()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("email outbox worker iteration failed")
            worked = False
        if not worked:
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.email_outbox_poll_seconds)
            except TimeoutError:
                pass
    logger.info("email outbox worker stopped")

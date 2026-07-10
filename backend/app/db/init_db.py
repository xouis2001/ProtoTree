from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import AgentSkillResource, AnalysisToolResource, CommercialProtocolResource, ContributionEvent, ImageMacroResource, Protocol, ProtocolCategory, ProtocolFolder, ProtocolStar, ProtocolTag, ProtocolTagGroup, User
from app.db.session import AsyncSessionLocal
from app.services.taxonomy import seed_taxonomy


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.url.get_backend_name().startswith("sqlite"):
            columns = await conn.execute(text("PRAGMA table_info(users)"))
            column_names = {row[1] for row in columns.fetchall()}
            if "avatar" not in column_names:
                await conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(80) NOT NULL DEFAULT '#2563eb|1111100110011111'"))
            if "is_admin" not in column_names:
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
            if "projects" not in column_names:
                await conn.execute(text("ALTER TABLE users ADD COLUMN projects JSON NOT NULL DEFAULT '[]'"))
            protocol_columns = await conn.execute(text("PRAGMA table_info(protocols)"))
            protocol_column_names = {row[1] for row in protocol_columns.fetchall()}
            if "folder_id" not in protocol_column_names:
                await conn.execute(text("ALTER TABLE protocols ADD COLUMN folder_id INTEGER REFERENCES protocol_folders(id) ON DELETE SET NULL"))
            if "source" not in protocol_column_names:
                await conn.execute(text("ALTER TABLE protocols ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'user'"))
            if "updated_at" not in protocol_column_names:
                await conn.execute(text("ALTER TABLE protocols ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"))
            first_user = await conn.execute(text("SELECT id FROM users ORDER BY id ASC LIMIT 1"))
            first_user_id = first_user.scalar_one_or_none()
            if first_user_id is not None:
                await conn.execute(text("UPDATE users SET is_admin = 1 WHERE id = :user_id"), {"user_id": first_user_id})
    async with AsyncSessionLocal() as session:
        await seed_taxonomy(session)

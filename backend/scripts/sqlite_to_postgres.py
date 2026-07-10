import json
import os
import sqlite3
from datetime import datetime

import psycopg2
from psycopg2.extras import Json


SQLITE_PATH = os.environ["SQLITE_PATH"]
PG_DSN = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)

TABLES = [
    "users",
    "protocol_categories",
    "protocol_tag_groups",
    "protocol_tags",
    "protocol_folders",
    "protocols",
    "protocol_stars",
    "contribution_events",
    "pitfalls",
    "comments",
    "image_macro_resources",
    "analysis_tool_resources",
    "agent_skill_resources",
    "commercial_protocol_resources",
]

JSON_COLUMNS = {
    "users": {"projects"},
    "protocols": {"structured"},
}
BOOLEAN_COLUMNS = {
    "users": {"is_admin"},
}


def convert_value(table: str, column: str, value):
    if value is None:
        return None
    if column in BOOLEAN_COLUMNS.get(table, set()):
        return bool(value)
    if column in JSON_COLUMNS.get(table, set()):
        if isinstance(value, str):
            return Json(json.loads(value or "null"))
        return Json(value)
    return value


def main():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(PG_DSN)

    try:
        with pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("SET session_replication_role = replica")
                for table in TABLES:
                    rows = sqlite_conn.execute(f'SELECT * FROM "{table}"').fetchall()
                    if not rows:
                        print(f"{table}: 0")
                        continue
                    columns = rows[0].keys()
                    column_sql = ", ".join(f'"{column}"' for column in columns)
                    placeholder_sql = ", ".join(["%s"] * len(columns))
                    update_sql = ", ".join(f'"{column}" = EXCLUDED."{column}"' for column in columns if column != "id")
                    conflict_sql = f'ON CONFLICT ("id") DO UPDATE SET {update_sql}' if update_sql else 'ON CONFLICT ("id") DO NOTHING'
                    sql = f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholder_sql}) {conflict_sql}'
                    values = [
                        tuple(convert_value(table, column, row[column]) for column in columns)
                        for row in rows
                    ]
                    cur.executemany(sql, values)
                    print(f"{table}: {len(rows)}")

                cur.execute("SET session_replication_role = DEFAULT")
                for table in TABLES:
                    cur.execute(
                        """
                        SELECT pg_get_serial_sequence(%s, 'id')
                        """,
                        (table,),
                    )
                    sequence = cur.fetchone()[0]
                    if sequence:
                        cur.execute(f'SELECT COALESCE(MAX(id), 0) FROM "{table}"')
                        max_id = cur.fetchone()[0]
                        cur.execute("SELECT setval(%s, %s, %s)", (sequence, max(max_id, 1), max_id > 0))
    finally:
        pg_conn.close()
        sqlite_conn.close()

    print(f"migration complete at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()

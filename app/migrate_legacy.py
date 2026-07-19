"""One-off migration helper.

The previous version of this project stored notices/messages in a
hand-rolled SQLite schema (see instance/database.db). This script reads
that legacy database and imports its rows into the new CMS schema so
nothing entered through the old admin panel is lost.

Usage:
    flask migrate-legacy [path/to/legacy/database.db]

Safe to run multiple times - it skips rows that look like duplicates
(same title) of ones already present.
"""
import sqlite3
from datetime import datetime, date

from . import models

db = models.db


def _parse_legacy_date(value: str) -> date:
    """Legacy notices stored dates like 'Jan 31, 2026'."""
    if not value:
        return date.today()
    for fmt in ("%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return date.today()


def migrate_legacy_db(legacy_path: str) -> dict:
    imported = {"notices": 0, "messages": 0}

    try:
        con = sqlite3.connect(legacy_path)
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not open legacy database at {legacy_path}: {exc}")

    con.row_factory = sqlite3.Row

    existing_notice_titles = {n.title for n in models.Notice.query.all()}
    try:
        for row in con.execute("SELECT * FROM notices"):
            if row["title"] in existing_notice_titles:
                continue
            db.session.add(models.Notice(
                title=row["title"],
                description=row["content"],
                publish_date=_parse_legacy_date(row["date"]),
            ))
            imported["notices"] += 1
    except sqlite3.OperationalError:
        pass  # legacy DB has no notices table

    existing_message_keys = {
        (m.name, m.email, m.message) for m in models.Message.query.all()
    }
    try:
        for row in con.execute("SELECT * FROM messages"):
            key = (row["name"], row["email"], row["message"])
            if key in existing_message_keys:
                continue
            db.session.add(models.Message(
                name=row["name"], email=row["email"], message=row["message"],
            ))
            imported["messages"] += 1
    except sqlite3.OperationalError:
        pass  # legacy DB has no messages table

    con.close()
    db.session.commit()
    return imported

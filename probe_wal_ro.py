import os
import platform
import sqlite3
import sys
import tempfile
from pathlib import Path


def build(td: Path, unlink_sidecars: bool) -> Path:
    db = td / "state_5.sqlite"
    c = sqlite3.connect(db)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE backfill_state(id INT, status TEXT)")
    c.execute("INSERT INTO backfill_state VALUES (1, 'complete')")
    c.commit()
    c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    c.close()
    if unlink_sidecars:
        for suf in ("-wal", "-shm"):
            p = Path(str(db) + suf)
            if p.exists():
                p.unlink()
    return db


def attempt(db: Path, query: str) -> str:
    try:
        con = sqlite3.connect(db.as_uri() + query, uri=True, timeout=1)
        row = con.execute("SELECT status FROM backfill_state WHERE id = 1").fetchone()
        con.close()
        return f"OK {row}"
    except sqlite3.Error as exc:
        return f"FAIL {type(exc).__name__}: {exc}"


print("platform:", platform.platform())
print("python:", sys.version.split()[0], "sqlite:", sqlite3.sqlite_version)
for unlink in (False, True):
    with tempfile.TemporaryDirectory() as t:
        td = Path(t)
        db = build(td, unlink)
        print(f"\nunlink_sidecars={unlink} files={sorted(os.listdir(td))}")
        for q in ("?mode=ro", "?mode=ro&immutable=1"):
            print(f"  {q:24} -> {attempt(db, q)}")
            print(f"  files after: {sorted(os.listdir(td))}")

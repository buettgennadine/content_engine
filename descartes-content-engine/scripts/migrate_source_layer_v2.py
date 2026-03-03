"""
Source Layer v2 Migration
Run on VPS: python scripts/migrate_source_layer_v2.py

1. Deactivates dead feeds (status='broken')
2. Adds content_utility column to articles
3. Adds frequency column to sources
4. Inserts new sources (dedup by URL)
"""
import sys
import json
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import get_connection
from config.uk_insurance import ALL_SOURCES, DEAD_FEEDS_TO_REMOVE


def migrate():
    conn = get_connection()
    c = conn.cursor()

    print("=== Source Layer v2 Migration ===\n")

    # 1. Add columns (safe: ignore if already exist)
    for ddl in [
        "ALTER TABLE articles ADD COLUMN content_utility TEXT DEFAULT 'D'",
        "ALTER TABLE sources ADD COLUMN frequency TEXT DEFAULT 'daily'",
    ]:
        try:
            c.execute(ddl)
            conn.commit()
            col = ddl.split("ADD COLUMN")[1].strip().split()[0]
            print(f"  [+] Column added: {col}")
        except Exception:
            pass  # already exists

    # 2. Deactivate dead feeds
    print("\nDeactivating dead feeds...")
    deactivated = 0
    for name in DEAD_FEEDS_TO_REMOVE:
        c.execute("UPDATE sources SET status='broken' WHERE name=?", (name,))
        if c.rowcount:
            print(f"  [-] Broken: {name}")
            deactivated += c.rowcount
    conn.commit()
    print(f"  Total deactivated: {deactivated}")

    # 3. Insert new sources (skip IMAP/PDF with no URL, skip duplicates by URL)
    print("\nInserting new sources...")
    inserted = 0
    skipped = 0
    for s in ALL_SOURCES:
        if not s.get("url"):
            continue
        c.execute("SELECT id FROM sources WHERE url=?", (s["url"],))
        if c.fetchone():
            skipped += 1
            continue
        cats = json.dumps([s["category"]] if s.get("category") else [])
        c.execute(
            """INSERT INTO sources (name, url, source_type, default_categories, tier, frequency, status)
               VALUES (?, ?, ?, ?, ?, ?, 'active')""",
            (s["name"], s["url"], s["source_type"], cats, s["tier"], s.get("frequency", "daily")),
        )
        print(f"  [+] Inserted: {s['name']}")
        inserted += 1
    conn.commit()
    print(f"  Inserted: {inserted} | Already existed: {skipped}")

    conn.close()
    print("\n=== Migration complete ===")
    print("\nNext steps:")
    print("  pm2 restart all")
    print("  python scripts/run_monitor.py --config uk_insurance --dry-run")
    print("  curl http://localhost:8000/api/sources | python -m json.tool | head -40")


if __name__ == "__main__":
    migrate()

"""
URL deduplication using SHA256 hash stored in SQLite.
"""
from core.database import article_exists, url_hash


def is_duplicate(url: str) -> bool:
    return article_exists(url)


def filter_new_articles(articles: list[dict]) -> list[dict]:
    """Remove articles already in the database."""
    new = [a for a in articles if not is_duplicate(a["url"])]
    duplicates = len(articles) - len(new)
    if duplicates:
        import logging
        logging.getLogger(__name__).debug(f"Filtered {duplicates} duplicates")
    return new

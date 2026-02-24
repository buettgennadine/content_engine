"""
RSS feed reader with error handling and deduplication.
"""
import feedparser
import logging
import requests
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Descartes-ContentEngine/1.0 (research@descartes-consulting.co.uk)"
}
TIMEOUT = 15


def fetch_feed(url: str) -> Optional[feedparser.FeedParserDict]:
    """Fetch and parse RSS feed. Returns None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            logger.warning(f"Malformed feed: {url}")
            return None
        return feed
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching: {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return None


def parse_date(entry) -> Optional[str]:
    """Try to extract a clean ISO date from a feed entry."""
    for field in ["published_parsed", "updated_parsed"]:
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6]).isoformat()
            except Exception:
                pass
    for field in ["published", "updated"]:
        val = getattr(entry, field, None)
        if val:
            try:
                return parsedate_to_datetime(val).isoformat()
            except Exception:
                pass
    return None


def get_snippet(entry) -> str:
    """Extract the best available text snippet from an entry."""
    for field in ["summary", "description", "content"]:
        val = getattr(entry, field, None)
        if val:
            if isinstance(val, list) and val:
                val = val[0].get("value", "")
            if val:
                # Strip HTML tags roughly
                import re
                clean = re.sub(r"<[^>]+>", " ", str(val))
                clean = " ".join(clean.split())
                return clean[:500]
    return ""


def fetch_articles_from_source(source: dict) -> list[dict]:
    """
    Given a source dict (from DB), fetch all new articles.
    Returns list of article dicts ready for classification.
    """
    url = source["url"]
    source_id = source["id"]

    feed = fetch_feed(url)
    if not feed:
        return []

    articles = []
    for entry in feed.entries[:50]:  # max 50 per run
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", "Untitled")
        if not link:
            continue

        articles.append({
            "url": link,
            "title": title,
            "source_id": source_id,
            "published_date": parse_date(entry),
            "snippet": get_snippet(entry),
        })

    logger.info(f"Fetched {len(articles)} entries from {source['name']}")
    return articles

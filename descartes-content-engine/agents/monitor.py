"""
Agent 1: Monitor
Runs every 6h via cron. Fetches all active RSS sources, classifies articles,
stores new ones in SQLite. No LLM for fetching — Claude Haiku for classification only.
"""
import logging
import time
from core import database as db
from core.rss_reader import fetch_articles_from_source
from core.imap_reader import fetch_newsletter_emails
from core.dedup import filter_new_articles
from core.llm import classify_article

logger = logging.getLogger(__name__)

MAX_API_CALLS_PER_MIN = 20
MIN_SCORE_TO_STORE = 6.0


def run(config_module, dry_run: bool = False):
    """
    Main entry point for Monitor agent.
    config_module: imported config (e.g. config.uk_insurance)
    """
    run_id = db.log_agent_run("monitor")
    logger.info("=== Monitor Agent starting ===")

    sources = db.get_active_sources(source_type="rss")
    if not sources:
        logger.info("No active sources in DB — seeding from config...")
        _seed_sources(config_module)
        sources = db.get_active_sources(source_type="rss")

    total_stored = 0
    api_calls = 0
    api_call_window_start = time.time()

    for source in sources:
        try:
            logger.info(f"Fetching: {source['name']}")
            raw_articles = fetch_articles_from_source(source)
            new_articles = filter_new_articles(raw_articles)

            if not new_articles:
                logger.debug(f"No new articles from {source['name']}")
                db.update_source_status(source["id"], success=True)
                continue

            for article in new_articles:
                # Rate limiting: max 20 API calls per minute
                if api_calls >= MAX_API_CALLS_PER_MIN:
                    elapsed = time.time() - api_call_window_start
                    if elapsed < 60:
                        wait = 60 - elapsed
                        logger.info(f"Rate limit pause: {wait:.1f}s")
                        time.sleep(wait)
                    api_calls = 0
                    api_call_window_start = time.time()

                categories = config_module.get_categories()
                classification = classify_article(
                    article["title"],
                    article.get("snippet", ""),
                    categories
                )
                api_calls += 1

                score = classification.get("relevance_score", 0)
                if score < MIN_SCORE_TO_STORE:
                    logger.debug(f"Score {score} < {MIN_SCORE_TO_STORE}, skipping: {article['title'][:60]}")
                    continue

                article.update({
                    "relevance_score": score,
                    "categories": classification.get("categories", []),
                    "urgency": classification.get("urgency", "evergreen"),
                    "content_angle": classification.get("content_angle", ""),
                    "data_points": classification.get("data_points", []),
                    "content_utility": classification.get("content_utility", "D"),
                })

                if not dry_run:
                    article_id = db.insert_article(article)
                    if article_id:
                        total_stored += 1
                        if score >= 9:
                            logger.warning(f"🔥 HIGH SCORE {score}: {article['title']}")

            db.update_source_status(source["id"], success=True)

        except Exception as e:
            logger.error(f"Error processing source {source['name']}: {e}")
            db.update_source_status(source["id"], success=False, error_msg=str(e))

    # IMAP newsletters
    try:
        newsletter_articles = fetch_newsletter_emails(limit=20)
        new_newsletters = filter_new_articles(newsletter_articles)
        for article in new_newsletters:
            categories = config_module.get_categories()
            classification = classify_article(
                article["title"],
                article.get("snippet", ""),
                categories
            )
            score = classification.get("relevance_score", 0)
            if score >= MIN_SCORE_TO_STORE:
                article.update({
                    "relevance_score": score,
                    "categories": classification.get("categories", []),
                    "urgency": classification.get("urgency", "evergreen"),
                    "content_angle": classification.get("content_angle", ""),
                    "data_points": classification.get("data_points", []),
                    "content_utility": classification.get("content_utility", "D"),
                })
                if not dry_run:
                    db.insert_article(article)
                    total_stored += 1
    except Exception as e:
        logger.error(f"IMAP fetch failed: {e}")

    logger.info(f"=== Monitor done. Stored {total_stored} new articles ===")
    db.finish_agent_run(run_id, status="success", articles=total_stored)
    return total_stored


def _seed_sources(config_module):
    """Seed RSS sources from config into DB."""
    import json
    conn = db.get_connection()
    try:
        sources = [s for s in config_module.get_all_sources() if s.get("url")]
        for s in sources:
            # Support both old format (categories list) and new format (category string)
            cats = s.get("categories") or ([s["category"]] if s.get("category") else [])
            conn.execute("""
                INSERT OR IGNORE INTO sources (name, url, source_type, tier, frequency, default_categories)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                s["name"], s["url"],
                s.get("source_type", "rss"),
                s.get("tier", 2),
                s.get("frequency", "daily"),
                json.dumps(cats),
            ))
        conn.commit()
        logger.info(f"Seeded {len(sources)} sources")
    finally:
        conn.close()

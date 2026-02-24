"""
Seed all RSS sources into the database.
Run once after setup, or re-run to add new sources (upsert-safe).

Usage:
    python scripts/seed_sources.py
    python scripts/seed_sources.py --config uk_insurance
    python scripts/seed_sources.py --config dach_insurance
"""
import sys
import argparse
from pathlib import Path

# Allow running from project root or scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import init_db, upsert_source


UK_SOURCES = [
    {"name": "FCA News", "url": "https://www.fca.org.uk/news/rss.xml", "tier": 1, "categories": ["regulatory_pressure"]},
    {"name": "Insurance Times", "url": "https://www.insurancetimes.co.uk/feed/", "tier": 1, "categories": ["claims_management", "industry_data"]},
    {"name": "ABI News", "url": "https://www.abi.org.uk/news/rss/", "tier": 1, "categories": ["industry_data", "regulatory_pressure"]},
    {"name": "FOS News", "url": "https://www.financial-ombudsman.org.uk/news/rss.xml", "tier": 1, "categories": ["claims_management", "consumer_duty"]},
    {"name": "Insurance Post", "url": "https://www.postonline.co.uk/feed", "tier": 2, "categories": ["claims_management"]},
    {"name": "Insurance Age", "url": "https://www.insuranceage.co.uk/feed", "tier": 2, "categories": ["claims_management"]},
    {"name": "The Actuary", "url": "https://www.theactuary.com/rss", "tier": 2, "categories": ["pension_operations", "industry_data"]},
    {"name": "TPR Press", "url": "https://www.thepensionsregulator.gov.uk/en/media-hub/press-releases.rss", "tier": 2, "categories": ["pension_operations", "regulatory_pressure"]},
    {"name": "Modern Insurance", "url": "https://www.modern-insurance-magazine.co.uk/feed/", "tier": 2, "categories": ["claims_technology", "digital_transformation"]},
    {"name": "Insurance Thought Leadership", "url": "https://insurancethoughtleadership.com/feed/", "tier": 2, "categories": ["systems_thinking", "claims_management"]},
    {"name": "Clyde & Co Insurance", "url": "https://www.clydeco.com/en/insights/rss?category=Insurance", "tier": 2, "categories": ["regulatory_pressure", "claims_management"]},
    {"name": "InsTech Podcast", "url": "https://www.instech.london/feed", "tier": 3, "categories": ["claims_technology"]},
]

DACH_SOURCES = [
    {"name": "VersicherungsJournal", "url": "https://www.versicherungsjournal.de/rss/versicherungsjournal.rss", "tier": 1, "categories": ["german_market", "claims_management", "industry_data"]},
    {"name": "GDV Pressemitteilungen", "url": "https://www.gdv.de/rss/presse.rss", "tier": 1, "categories": ["german_market", "regulatory_pressure", "industry_data", "combined_ratio"]},
    {"name": "BaFin Meldungen", "url": "https://www.bafin.de/SiteGlobals/Functions/RSS/DE/Feed/RSSNewsFeed_Meldungen.xml", "tier": 1, "categories": ["german_market", "regulatory_pressure"]},
    {"name": "Versicherungswirtschaft heute", "url": "https://versicherungswirtschaft-heute.de/feed/", "tier": 2, "categories": ["german_market", "industry_data", "digital_transformation"]},
    {"name": "Versicherungsbote", "url": "https://www.versicherungsbote.de/rss/", "tier": 2, "categories": ["german_market", "claims_management"]},
    {"name": "AssCompact", "url": "https://www.asscompact.de/feed", "tier": 2, "categories": ["german_market", "bav"]},
    {"name": "Map-Report (Franke & Bornberg)", "url": "https://map-report.com/feed", "tier": 2, "categories": ["german_market", "industry_data", "combined_ratio"]},
    {"name": "Versicherungsforen Leipzig Blog", "url": "https://blog.versicherungsforen.net/feed/", "tier": 2, "categories": ["german_market", "systems_thinking", "digital_transformation"]},
    {"name": "VJ Medienspiegel", "url": "https://www.versicherungsjournal.de/rss/medienspiegel.rss", "tier": 3, "categories": ["german_market"]},
    {"name": "Tagesbriefing.de", "url": "https://tagesbriefing.de/feed/", "tier": 3, "categories": ["german_market"]},
]

SUBSTACK_SOURCES = [
    {"name": "Claims Journal", "url": "https://www.claimsjournal.com/feed/", "tier": 2, "categories": ["claims_management"]},
    {"name": "Think Different (FlowChainSensei)", "url": "https://flowchainsensei.wordpress.com/feed/", "tier": 2, "categories": ["systems_thinking", "toc_lean"]},
    {"name": "Squire to the Giants", "url": "https://squiretothegiant.com/feed/", "tier": 2, "categories": ["systems_thinking", "toc_lean"]},
    {"name": "Open Insurance Observatory", "url": "https://openinsuranceobs.substack.com/feed", "tier": 2, "categories": ["german_market", "digital_transformation"]},
    {"name": "Merantix Capital Insurance", "url": "https://merantixcapital.substack.com/feed", "tier": 2, "categories": ["german_market", "claims_technology"]},
    {"name": "Dragan's Newsletter TOC", "url": "https://dragannastic.substack.com/feed", "tier": 3, "categories": ["toc_lean"]},
    {"name": "TOC for Startups", "url": "https://tocforstartups.substack.com/feed", "tier": 3, "categories": ["toc_lean"]},
]

REDDIT_SOURCES = [
    {"name": "r/UKPersonalFinance", "url": "https://www.reddit.com/r/UKPersonalFinance.rss?limit=25", "tier": 2, "categories": ["consumer_duty", "pension_operations"]},
    {"name": "r/ActuaryUK", "url": "https://www.reddit.com/r/ActuaryUK.rss?limit=25", "tier": 2, "categories": ["pension_operations"]},
    {"name": "r/Insurance", "url": "https://www.reddit.com/r/Insurance.rss?limit=25", "tier": 3, "categories": ["claims_management"]},
    {"name": "r/systemsthinking", "url": "https://www.reddit.com/r/systemsthinking.rss?limit=25", "tier": 3, "categories": ["systems_thinking"]},
    {"name": "r/FIREUK", "url": "https://www.reddit.com/r/FIREUK.rss?limit=25", "tier": 3, "categories": ["pension_operations"]},
]


def seed_all():
    init_db()
    all_sources = UK_SOURCES + DACH_SOURCES + SUBSTACK_SOURCES + REDDIT_SOURCES
    print(f"Seeding {len(all_sources)} sources...")
    for s in all_sources:
        upsert_source(
            name=s["name"],
            url=s["url"],
            source_type="rss",
            tier=s["tier"],
            categories=s["categories"],
        )
        print(f"  ✓ {s['name']}")
    print(f"\nDone. {len(all_sources)} sources registered in DB.")


def seed_uk():
    init_db()
    sources = UK_SOURCES + SUBSTACK_SOURCES + REDDIT_SOURCES
    print(f"Seeding {len(sources)} UK + shared sources...")
    for s in sources:
        upsert_source(name=s["name"], url=s["url"], source_type="rss", tier=s["tier"], categories=s["categories"])
        print(f"  ✓ {s['name']}")
    print(f"\nDone. {len(sources)} sources registered.")


def seed_dach():
    init_db()
    sources = DACH_SOURCES
    print(f"Seeding {len(sources)} DACH sources...")
    for s in sources:
        upsert_source(name=s["name"], url=s["url"], source_type="rss", tier=s["tier"], categories=s["categories"])
        print(f"  ✓ {s['name']}")
    print(f"\nDone. {len(sources)} DACH sources registered.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed RSS sources into database.")
    parser.add_argument("--config", choices=["uk_insurance", "dach_insurance", "all"], default="all")
    args = parser.parse_args()

    if args.config == "uk_insurance":
        seed_uk()
    elif args.config == "dach_insurance":
        seed_dach()
    else:
        seed_all()

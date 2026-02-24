"""
Instance 2: Stuart Corrigan — DACH Insurance Market
RSS sources, categories, and config for the German-speaking market.
All content is classified and output in English.
"""

INSTANCE_NAME = "dach_insurance"
CONSULTANT_NAME = "Stuart Corrigan"
COMPANY = "Descartes Consulting Ltd"
TARGET_MARKETS = ["DACH", "DE", "AT", "CH"]

# Categories used for article classification
CATEGORIES = [
    "claims_management",
    "pension_operations",
    "regulatory_pressure",
    "systems_thinking",
    "toc_lean",
    "digital_transformation",
    "industry_data",
    "german_market",
    "claims_technology",
    "combined_ratio",
    "bav",  # Betriebliche Altersversorgung
]

# RSS Sources — DACH (Tier 1 = most important)
DACH_RSS_SOURCES = [
    {
        "name": "VersicherungsJournal",
        "url": "https://www.versicherungsjournal.de/rss/versicherungsjournal.rss",
        "tier": 1,
        "categories": ["german_market", "claims_management", "industry_data"],
        "language": "de",
    },
    {
        "name": "GDV Pressemitteilungen",
        "url": "https://www.gdv.de/rss/presse.rss",
        "tier": 1,
        "categories": ["german_market", "regulatory_pressure", "industry_data", "combined_ratio"],
        "language": "de",
    },
    {
        "name": "BaFin Meldungen",
        "url": "https://www.bafin.de/SiteGlobals/Functions/RSS/DE/Feed/RSSNewsFeed_Meldungen.xml",
        "tier": 1,
        "categories": ["german_market", "regulatory_pressure"],
        "language": "de",
    },
    {
        "name": "Versicherungswirtschaft heute",
        "url": "https://versicherungswirtschaft-heute.de/feed/",
        "tier": 2,
        "categories": ["german_market", "industry_data", "digital_transformation"],
        "language": "de",
    },
    {
        "name": "Versicherungsbote",
        "url": "https://www.versicherungsbote.de/rss/",
        "tier": 2,
        "categories": ["german_market", "claims_management"],
        "language": "de",
    },
    {
        "name": "AssCompact",
        "url": "https://www.asscompact.de/feed",
        "tier": 2,
        "categories": ["german_market", "bav"],
        "language": "de",
    },
    {
        "name": "Map-Report (Franke & Bornberg)",
        "url": "https://map-report.com/feed",
        "tier": 2,
        "categories": ["german_market", "industry_data", "combined_ratio"],
        "language": "de",
    },
    {
        "name": "Versicherungsforen Leipzig Blog",
        "url": "https://blog.versicherungsforen.net/feed/",
        "tier": 2,
        "categories": ["german_market", "systems_thinking", "digital_transformation"],
        "language": "de",
    },
    {
        "name": "VJ Medienspiegel",
        "url": "https://www.versicherungsjournal.de/rss/medienspiegel.rss",
        "tier": 3,
        "categories": ["german_market"],
        "language": "de",
    },
    {
        "name": "Tagesbriefing.de",
        "url": "https://tagesbriefing.de/feed/",
        "tier": 3,
        "categories": ["german_market"],
        "language": "de",
    },
]

# Substacks & Blogs — Systems Thinking / TOC / InsurTech
SUBSTACK_SOURCES = [
    {
        "name": "Claims Journal",
        "url": "https://www.claimsjournal.com/feed/",
        "tier": 2,
        "categories": ["claims_management"],
        "language": "en",
    },
    {
        "name": "Think Different (FlowChainSensei)",
        "url": "https://flowchainsensei.wordpress.com/feed/",
        "tier": 2,
        "categories": ["systems_thinking", "toc_lean"],
        "language": "en",
    },
    {
        "name": "Squire to the Giants",
        "url": "https://squiretothegiant.com/feed/",
        "tier": 2,
        "categories": ["systems_thinking", "toc_lean"],
        "language": "en",
    },
    {
        "name": "Open Insurance Observatory",
        "url": "https://openinsuranceobs.substack.com/feed",
        "tier": 2,
        "categories": ["german_market", "digital_transformation"],
        "language": "en",
    },
    {
        "name": "Merantix Capital Insurance",
        "url": "https://merantixcapital.substack.com/feed",
        "tier": 2,
        "categories": ["german_market", "claims_technology"],
        "language": "en",
    },
    {
        "name": "Dragan's Newsletter TOC",
        "url": "https://dragannastic.substack.com/feed",
        "tier": 3,
        "categories": ["toc_lean"],
        "language": "en",
    },
    {
        "name": "TOC for Startups",
        "url": "https://tocforstartups.substack.com/feed",
        "tier": 3,
        "categories": ["toc_lean"],
        "language": "en",
    },
]

# Reddit RSS — Consumer signals & professional insights
REDDIT_SOURCES = [
    {
        "name": "r/Insurance",
        "url": "https://www.reddit.com/r/Insurance.rss?limit=25",
        "tier": 2,
        "categories": ["claims_management"],
        "language": "en",
    },
    {
        "name": "r/systemsthinking",
        "url": "https://www.reddit.com/r/systemsthinking.rss?limit=25",
        "tier": 2,
        "categories": ["systems_thinking", "toc_lean"],
        "language": "en",
    },
    {
        "name": "r/UKPersonalFinance",
        "url": "https://www.reddit.com/r/UKPersonalFinance.rss?limit=25",
        "tier": 3,
        "categories": ["pension_operations"],
        "language": "en",
    },
    {
        "name": "r/ActuaryUK",
        "url": "https://www.reddit.com/r/ActuaryUK.rss?limit=25",
        "tier": 3,
        "categories": ["pension_operations"],
        "language": "en",
    },
    {
        "name": "r/FIREUK",
        "url": "https://www.reddit.com/r/FIREUK.rss?limit=25",
        "tier": 3,
        "categories": ["pension_operations"],
        "language": "en",
    },
]

ALL_RSS_SOURCES = DACH_RSS_SOURCES + SUBSTACK_SOURCES + REDDIT_SOURCES
SOURCES = ALL_RSS_SOURCES


def get_all_sources():
    return ALL_RSS_SOURCES


def get_categories():
    return CATEGORIES

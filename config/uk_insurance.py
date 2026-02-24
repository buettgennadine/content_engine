"""
Instance 1: Stuart Corrigan — UK Insurance Market
RSS sources, categories, and config for the UK market.

Note: DACH sources are handled by config/dach_insurance.py
"""

INSTANCE_NAME = "uk_insurance"
CONSULTANT_NAME = "Stuart Corrigan"
COMPANY = "Descartes Consulting Ltd"
TARGET_MARKETS = ["UK"]

# Categories used for article classification
CATEGORIES = [
    "claims_management",
    "pension_operations",
    "regulatory_pressure",
    "systems_thinking",
    "toc_lean",
    "digital_transformation",
    "consumer_duty",
    "industry_data",
    "claims_technology",
]

# RSS Sources — UK (Tier 1 = most important)
UK_RSS_SOURCES = [
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

# Substacks & Blogs (shared with DACH instance)
SUBSTACK_SOURCES = [
    {"name": "Claims Journal", "url": "https://www.claimsjournal.com/feed/", "tier": 2, "categories": ["claims_management"]},
    {"name": "Think Different (FlowChainSensei)", "url": "https://flowchainsensei.wordpress.com/feed/", "tier": 2, "categories": ["systems_thinking", "toc_lean"]},
    {"name": "Squire to the Giants", "url": "https://squiretothegiant.com/feed/", "tier": 2, "categories": ["systems_thinking", "toc_lean"]},
    {"name": "Dragan's Newsletter TOC", "url": "https://dragannastic.substack.com/feed", "tier": 3, "categories": ["toc_lean"]},
    {"name": "TOC for Startups", "url": "https://tocforstartups.substack.com/feed", "tier": 3, "categories": ["toc_lean"]},
]

# Reddit RSS (shared with DACH instance)
REDDIT_SOURCES = [
    {"name": "r/UKPersonalFinance", "url": "https://www.reddit.com/r/UKPersonalFinance.rss?limit=25", "tier": 2, "categories": ["consumer_duty", "pension_operations"]},
    {"name": "r/ActuaryUK", "url": "https://www.reddit.com/r/ActuaryUK.rss?limit=25", "tier": 2, "categories": ["pension_operations"]},
    {"name": "r/Insurance", "url": "https://www.reddit.com/r/Insurance.rss?limit=25", "tier": 3, "categories": ["claims_management"]},
    {"name": "r/systemsthinking", "url": "https://www.reddit.com/r/systemsthinking.rss?limit=25", "tier": 3, "categories": ["systems_thinking"]},
    {"name": "r/FIREUK", "url": "https://www.reddit.com/r/FIREUK.rss?limit=25", "tier": 3, "categories": ["pension_operations"]},
]

ALL_RSS_SOURCES = UK_RSS_SOURCES + SUBSTACK_SOURCES + REDDIT_SOURCES
SOURCES = ALL_RSS_SOURCES


def get_all_sources():
    return ALL_RSS_SOURCES


def get_categories():
    return CATEGORIES

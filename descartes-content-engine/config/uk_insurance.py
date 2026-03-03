"""
Instance 1: Stuart Corrigan — UK Insurance Market
Source Layer v2 — repriorisiert nach Content Utility.
"""

INSTANCE_NAME = "uk_insurance"
CONSULTANT_NAME = "Stuart Corrigan"
COMPANY = "Descartes Consulting Ltd"
TARGET_MARKETS = ["UK", "DACH"]

# Categories v2 (6 categories, replacing old 10-category system)
CATEGORIES = [
    "cross_industry",    # Kat 1: Cross-Industry Ops
    "claims_pensions",   # Kat 2: Claims/Pensions Pain-Data
    "research",          # Kat 3: Academic/research
    "industry",          # Kat 4: Insurance industry news (radikal gekuerzt)
    "thought_leaders",   # Kat 5: Thought leader feeds
    "viral_transfer",    # Kat 6: Viral transfer stories
]

# ─── Kat 1: Cross-Industry Ops (35%) ─────────────────────────────────────────

SOURCES_CROSS_INDUSTRY_RSS = [
    {"name": "HBR", "url": "https://feeds.feedburner.com/harvardbusiness", "source_type": "rss", "category": "cross_industry", "tier": 1, "frequency": "daily"},
    {"name": "McKinsey Insights", "url": "https://www.mckinsey.com/insights/rss", "source_type": "rss", "category": "cross_industry", "tier": 1, "frequency": "weekly"},
    {"name": "Lean Enterprise Inst", "url": "https://www.lean.org/feed/", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "weekly"},
    {"name": "Farnam Street", "url": "https://fs.blog/feed/", "source_type": "rss", "category": "cross_industry", "tier": 1, "frequency": "weekly"},
    {"name": "OPS Group Aviation", "url": "https://ops.group/blog/feed/", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "weekly"},
    {"name": "Mark Graban Lean Blog", "url": "https://www.leanblog.org/feed/", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "weekly"},
    {"name": "Beyond Lean", "url": "https://beyondlean.wordpress.com/feed/", "source_type": "rss", "category": "cross_industry", "tier": 3, "frequency": "monthly"},
    {"name": "Science of Business TOC", "url": "https://scienceofbusiness.com/feed/", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "monthly"},
    {"name": "INFORMS", "url": "https://informs.org/rss/feed/iol_news", "source_type": "rss", "category": "cross_industry", "tier": 3, "frequency": "weekly"},
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "daily"},
]

SOURCES_CROSS_INDUSTRY_GOOGLE = [
    {"name": "GNews Operational Failure", "url": "https://news.google.com/rss/search?q=operational+failure+backlog&hl=en-GB", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "daily"},
    {"name": "GNews Service Ops Failure", "url": "https://news.google.com/rss/search?q=%22service+operations%22+failure+OR+backlog&hl=en-GB", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "daily"},
    {"name": "GNews WIP Limits", "url": "https://news.google.com/rss/search?q=%22work+in+progress%22+limits+operations&hl=en-GB", "source_type": "rss", "category": "cross_industry", "tier": 3, "frequency": "daily"},
    {"name": "GNews TOC", "url": "https://news.google.com/rss/search?q=%22theory+of+constraints%22&hl=en-GB", "source_type": "rss", "category": "cross_industry", "tier": 1, "frequency": "daily"},
]

SOURCES_CROSS_INDUSTRY_SUBSTACK = [
    {"name": "Scott Galloway", "url": "https://www.profgalloway.com/feed/", "source_type": "rss", "category": "cross_industry", "tier": 1, "frequency": "weekly"},
    {"name": "FlowChainSensei", "url": "https://flowchainsensei.substack.com/feed", "source_type": "rss", "category": "cross_industry", "tier": 2, "frequency": "weekly"},
]

SOURCES_CROSS_INDUSTRY_PODCASTS = [
    {"name": "More or Less BBC", "url": "https://podcasts.files.bbci.co.uk/p02nrss1.rss", "source_type": "rss", "category": "cross_industry", "tier": 3, "frequency": "weekly"},
    {"name": "LEI Podcast", "url": "https://feed.podbean.com/lei/feed.xml", "source_type": "rss", "category": "cross_industry", "tier": 3, "frequency": "weekly"},
]

# ─── Kat 2: Claims/Pensions Pain-Data (25%) ──────────────────────────────────

SOURCES_PAIN_DATA_REGULATORY = [
    {"name": "FCA News", "url": "https://www.fca.org.uk/news/rss.xml", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
    {"name": "FOS News", "url": "https://www.financial-ombudsman.org.uk/news/rss", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "weekly"},
    {"name": "NHS England", "url": "https://www.england.nhs.uk/feed/", "source_type": "rss", "category": "claims_pensions", "tier": 2, "frequency": "daily"},
]

SOURCES_PAIN_DATA_GOOGLE = [
    {"name": "GNews Claims Backlog UK", "url": "https://news.google.com/rss/search?q=claims+insurance+UK+backlog&hl=en-GB", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
    {"name": "GNews Consumer Duty", "url": "https://news.google.com/rss/search?q=%22Consumer+Duty%22+complaints+insurance&hl=en-GB", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
    {"name": "GNews Pension Backlog", "url": "https://news.google.com/rss/search?q=pension+administration+backlog+UK&hl=en-GB", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
    {"name": "GNews Failure Demand", "url": "https://news.google.com/rss/search?q=%22failure+demand%22&hl=en-GB", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
    {"name": "GNews Customer Effort", "url": "https://news.google.com/rss/search?q=%22customer+effort%22+service+redesign&hl=en-GB", "source_type": "rss", "category": "claims_pensions", "tier": 2, "frequency": "daily"},
    {"name": "GNews Schadenbearbeitung DE", "url": "https://news.google.com/rss/search?q=Schadenbearbeitung+Versicherung&hl=de", "source_type": "rss", "category": "claims_pensions", "tier": 2, "frequency": "daily"},
    {"name": "GNews bAV Digitalisierung DE", "url": "https://news.google.com/rss/search?q=bAV+Digitalisierung+betriebliche+Altersversorgung&hl=de", "source_type": "rss", "category": "claims_pensions", "tier": 2, "frequency": "daily"},
    {"name": "GNews Combined Ratio DE", "url": "https://news.google.com/rss/search?q=Versicherung+Schadenquote+Combined+Ratio&hl=de", "source_type": "rss", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
]

SOURCES_PAIN_DATA_IMAP = [
    {"name": "Oxbow Partners", "url": "", "source_type": "imap", "category": "claims_pensions", "tier": 1, "frequency": "weekly"},
    {"name": "Insurance Insider", "url": "", "source_type": "imap", "category": "claims_pensions", "tier": 1, "frequency": "daily"},
]

SOURCES_PAIN_DATA_PDF = [
    {"name": "FCA Complaints Data", "url": "", "source_type": "pdf_scrape", "category": "claims_pensions", "tier": 1, "frequency": "biannual"},
    {"name": "FOS Annual Report", "url": "", "source_type": "pdf_scrape", "category": "claims_pensions", "tier": 1, "frequency": "annual"},
]

# ─── Kat 3: Research (10%) ────────────────────────────────────────────────────

SOURCES_RESEARCH = [
    {"name": "Behavioral Scientist", "url": "https://behavioralscientist.org/feed/", "source_type": "rss", "category": "research", "tier": 2, "frequency": "weekly"},
    {"name": "BMJ Quality Safety", "url": "https://qualitysafety.bmj.com/rss/current.xml", "source_type": "rss", "category": "research", "tier": 2, "frequency": "monthly"},
    {"name": "BMJ Open Quality", "url": "https://bmjopenquality.bmj.com/rss/current.xml", "source_type": "rss", "category": "research", "tier": 3, "frequency": "monthly"},
    {"name": "INFORMS Research", "url": "https://informs.org/rss/feed/iol_news", "source_type": "rss", "category": "research", "tier": 3, "frequency": "weekly"},
]

# ─── Kat 4: Industry News (10%) — radikal gekuerzt ────────────────────────────

SOURCES_INDUSTRY = [
    {"name": "Versicherungsbote", "url": "https://www.versicherungsbote.de/feed/", "source_type": "rss", "category": "industry", "tier": 2, "frequency": "daily"},
    {"name": "VW heute", "url": "https://versicherungswirtschaft-heute.de/feed/", "source_type": "rss", "category": "industry", "tier": 2, "frequency": "daily"},
    {"name": "Pulse Today", "url": "https://www.pulsetoday.co.uk/feed/", "source_type": "rss", "category": "industry", "tier": 3, "frequency": "daily"},
    {"name": "FT Companies", "url": "https://www.ft.com/companies?format=rss", "source_type": "rss", "category": "industry", "tier": 2, "frequency": "daily"},
]

# ─── Kat 5: Thought Leader Feeds (10%) ───────────────────────────────────────

SOURCES_THOUGHT_LEADERS = [
    {"name": "Lencioni At The Table", "url": "https://feeds.captivate.fm/at-the-table/", "source_type": "rss", "category": "thought_leaders", "tier": 2, "frequency": "weekly"},
    {"name": "Deming Institute", "url": "https://deming.org/feed/", "source_type": "rss", "category": "thought_leaders", "tier": 1, "frequency": "monthly"},
    {"name": "Beyond Command Control Seddon", "url": "https://beyondcommandandcontrol.com/feed/", "source_type": "rss", "category": "thought_leaders", "tier": 1, "frequency": "monthly"},
    {"name": "Seth Godin", "url": "https://feeds.feedblitz.com/SethsBlog", "source_type": "rss", "category": "thought_leaders", "tier": 2, "frequency": "daily"},
    {"name": "Simon Sinek", "url": "https://simonsinek.com/feed/", "source_type": "rss", "category": "thought_leaders", "tier": 2, "frequency": "weekly"},
    {"name": "Science of Business TOC TL", "url": "https://scienceofbusiness.com/feed/", "source_type": "rss", "category": "thought_leaders", "tier": 2, "frequency": "monthly"},
]

# ─── Kat 6: Viral Transfer Stories (10%) ─────────────────────────────────────

SOURCES_VIRAL_TRANSFER = [
    {"name": "GNews Business Failure Lessons", "url": "https://news.google.com/rss/search?q=business+failure+lessons+learned&hl=en-GB", "source_type": "rss", "category": "viral_transfer", "tier": 2, "frequency": "daily"},
    {"name": "GNews Operational Turnaround", "url": "https://news.google.com/rss/search?q=company+turnaround+OR+%22operational+turnaround%22&hl=en-GB", "source_type": "rss", "category": "viral_transfer", "tier": 2, "frequency": "daily"},
    {"name": "GNews Backlog Crisis", "url": "https://news.google.com/rss/search?q=backlog+crisis+UK+2025+OR+2026&hl=en-GB", "source_type": "rss", "category": "viral_transfer", "tier": 2, "frequency": "daily"},
]

# ─── Aggregation ──────────────────────────────────────────────────────────────

ALL_SOURCES = (
    SOURCES_CROSS_INDUSTRY_RSS
    + SOURCES_CROSS_INDUSTRY_GOOGLE
    + SOURCES_CROSS_INDUSTRY_SUBSTACK
    + SOURCES_CROSS_INDUSTRY_PODCASTS
    + SOURCES_PAIN_DATA_REGULATORY
    + SOURCES_PAIN_DATA_GOOGLE
    + SOURCES_PAIN_DATA_IMAP
    + SOURCES_PAIN_DATA_PDF
    + SOURCES_RESEARCH
    + SOURCES_INDUSTRY
    + SOURCES_THOUGHT_LEADERS
    + SOURCES_VIRAL_TRANSFER
)

# Dead feeds to deactivate (status='broken') — 22 URLs + Reddit
DEAD_FEEDS_TO_REMOVE = [
    "Insurance Times",
    "Insurance Post",
    "Insurance Age",
    "The Actuary",
    "ABI News",
    "Clyde & Co Insurance",
    "InsTech Podcast",
    "Modern Insurance",
    "Insurance Thought Leadership",
    "TPR Press",
    "VersicherungsJournal",
    "VJ Medienspiegel",
    "BaFin Meldungen",
    "GDV Pressemitteilungen",
    "AssCompact",
    "Map-Report",
    "Versicherungsforen Leipzig Blog",
    "Claims Journal",
    "Think Different (FlowChainSensei)",
    "Squire to the Giants",
    "Dragan's Newsletter TOC",
    "TOC for Startups",
    "r/UKPersonalFinance",
    "r/ActuaryUK",
    "r/insurance",
    "r/systemsthinking",
]


def get_all_sources():
    return ALL_SOURCES


def get_rss_sources():
    return [s for s in ALL_SOURCES if s["source_type"] == "rss" and s["url"]]


def get_categories():
    return CATEGORIES

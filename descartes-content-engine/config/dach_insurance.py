"""
DACH Insurance Market + Substacks + Reddit — Source Configuration
Instance 2: Germany expansion sources.
"""

INSTANCE_NAME = "dach_insurance"

SOURCES = [
    # ── Tier 1: DACH Regulatory & High-Signal ──────────────────────────────
    {
        "name": "BaFin Meldungen",
        "url": "https://www.bafin.de/SiteGlobals/Functions/RSS/DE/rss_Meldungen.xml",
        "tier": 1,
        "categories": ["regulatory", "germany"],
    },
    {
        "name": "GDV Pressemitteilungen",
        "url": "https://www.gdv.de/gdv/presse/rss",
        "tier": 1,
        "categories": ["industry", "germany"],
    },
    {
        "name": "VersicherungsJournal",
        "url": "https://www.versicherungsjournal.de/rss/",
        "tier": 1,
        "categories": ["claims", "germany"],
    },
    # ── Tier 2: DACH Trade Press ────────────────────────────────────────────
    {
        "name": "VJ Medienspiegel",
        "url": "https://www.versicherungsjournal.de/rss/medienspiegel.xml",
        "tier": 2,
        "categories": ["industry", "germany"],
    },
    {
        "name": "Versicherungsbote",
        "url": "https://www.versicherungsbote.de/rss/",
        "tier": 2,
        "categories": ["industry", "germany"],
    },
    {
        "name": "Versicherungswirtschaft heute",
        "url": "https://www.vwheute.de/rss",
        "tier": 2,
        "categories": ["industry", "germany"],
    },
    {
        "name": "AssCompact",
        "url": "https://www.asscompact.de/rss/alle-nachrichten",
        "tier": 2,
        "categories": ["industry", "germany"],
    },
    {
        "name": "Versicherungsforen Leipzig Blog",
        "url": "https://www.versicherungsforen.net/blog/feed/",
        "tier": 2,
        "categories": ["transformation", "germany"],
    },

    # ── Substacks & TOC Blogs ───────────────────────────────────────────────
    {
        "name": "Open Insurance Observatory",
        "url": "https://openinsurance.substack.com/feed",
        "tier": 2,
        "categories": ["technology", "transformation"],
    },
    {
        "name": "Dragan's Newsletter (TOC/Lean)",
        "url": "https://dragans.substack.com/feed",
        "tier": 2,
        "categories": ["toc"],
    },
    {
        "name": "TOC for Startups",
        "url": "https://tocforstartups.substack.com/feed",
        "tier": 2,
        "categories": ["toc"],
    },
    {
        "name": "FlowChainSensei (Vanguard/Seddon)",
        "url": "https://flowchainsensei.wordpress.com/feed/",
        "tier": 2,
        "categories": ["toc", "transformation"],
    },
    {
        "name": "Squire to the Giants (Deming/Ohno)",
        "url": "https://squiretothegiantscom.wordpress.com/feed/",
        "tier": 2,
        "categories": ["toc"],
    },

    # ── Reddit RSS ──────────────────────────────────────────────────────────
    {
        "name": "Reddit: UKPersonalFinance",
        "url": "https://www.reddit.com/r/UKPersonalFinance/.rss",
        "tier": 3,
        "categories": ["claims", "pension"],
    },
    {
        "name": "Reddit: insurance",
        "url": "https://www.reddit.com/r/insurance/.rss",
        "tier": 3,
        "categories": ["claims"],
    },
    {
        "name": "Reddit: systemsthinking",
        "url": "https://www.reddit.com/r/systemsthinking/.rss",
        "tier": 3,
        "categories": ["toc"],
    },
    {
        "name": "Reddit: ActuaryUK",
        "url": "https://www.reddit.com/r/ActuaryUK/.rss",
        "tier": 3,
        "categories": ["pension"],
    },
    {
        "name": "Reddit: FIREUK",
        "url": "https://www.reddit.com/r/FIREUK/.rss",
        "tier": 3,
        "categories": ["pension"],
    },
]

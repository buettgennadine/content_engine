"""
Initialise database and seed:
1. All pain points from Master SKILL
2. All RSS sources from both configs
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from core.database import init_db, upsert_source, insert_pain_point, get_connection

PAIN_POINTS = [
    # UK Claims
    ("FOS complaints volume", "305,726 (2024/25, +54%)", "FCA/FOS Annual Report 2025", "2025", "uk_claims", "UK"),
    ("Claims % of GI complaints", "71% of all GI complaints", "FOS Annual Report 2025", "2025", "uk_claims", "UK"),
    ("Motor claims record", "£11.7B total (2024, +17%)", "ABI Motor Claims Report 2024", "2024", "uk_claims", "UK"),
    ("Average motor claim Q4 2024", "£5,300", "ABI Statistics 2024", "2024", "uk_claims", "UK"),
    ("Property claims 2025", "£6.1B record", "ABI 2025", "2025", "uk_claims", "UK"),
    ("Combined ratio UK GI", "£1.18 per £1 premium (5th consecutive loss year)", "ABI 2024", "2024", "uk_claims", "UK"),
    ("Staff shortages in UK insurance", "72% of UK insurers struggling", "Insurance Times Survey 2024", "2024", "uk_claims", "UK"),
    ("Legacy IT as digitisation blocker", "9 out of 10 cite it", "Insurance Post Survey 2024", "2024", "uk_claims", "UK"),
    ("Storm claims payout rate 2024", "Only 32% paid (FCA review)", "FCA Consumer Duty Review 2024", "2024", "uk_claims", "UK"),
    ("Claims handler workforce decline", "60% forecast decline over next decade", "LCP/Actuarial Survey 2024", "2024", "uk_claims", "UK"),
    ("Straight-through processing (STP) rate", "7% industry average vs 57% AI-first insurers", "McKinsey Insurance Report 2024", "2024", "uk_claims", "UK"),
    ("Claims leakage range", "5-18% (audit average 11%)", "Verisk/ISO Claims Benchmark 2024", "2024", "uk_claims", "UK"),

    # UK Pensions
    ("Pensions Dashboard delay", "2023 → 31 Oct 2026 (cost overrun £235m → £289m, +23%)", "DWP/MaPS Update 2024", "2024", "uk_pensions", "UK"),
    ("Pension admin recruitment challenge", "80% of pension admins struggling with recruitment", "Pensions Management Institute Survey 2024", "2024", "uk_pensions", "UK"),
    ("Regulatory complexity as barrier", "58% cite it as top-3 challenge", "PMI Industry Survey 2024", "2024", "uk_pensions", "UK"),

    # Germany
    ("German nat-cat claims growth", "+28% annually (2020-2023)", "GDV Statistisches Taschenbuch 2024", "2024", "germany", "DE"),
    ("Average German motor claim", "~€4,000 (+8.6% YoY)", "GDV 2024", "2024", "germany", "DE"),
    ("German claims automation range", "4%-40% (leaders: 80% for glass claims)", "Versicherungsforen Leipzig Report 2024", "2024", "germany", "DE"),
    ("bAV admin complexity", "Too complex for 50% of companies", "GDV bAV Report 2024", "2024", "germany", "DE"),
    ("German insurer digitisation plans", "62% plan digitisation without systems thinking", "Versicherungsforen Leipzig 2024", "2024", "germany", "DE"),

    # Systems Thinking
    ("Failure demand in service orgs", "40-60% (Seddon/Vanguard research)", "Vanguard Consulting 2023", "2023", "systems_thinking", "UK"),
    ("Documented extreme failure demand", "70% failure demand, 2.5 transactions per customer", "Vanguard Case Study (anonymised)", "2022", "systems_thinking", "UK"),
    ("WIP reduction outcome", "700 → 300 staff after redesign, work returned from India to UK", "Vanguard/Descartes Case Study", "2023", "systems_thinking", "UK"),
]

UK_IMAP_SOURCE = {
    "name": "Newsletter IMAP (descartes.research@gmail.com)",
    "url": "imap://descartes.research@gmail.com",
    "source_type": "imap",
    "tier": 1,
    "categories": ["regulatory", "industry", "toc"],
}


def seed_pain_points():
    print("Seeding pain points...")
    count = 0
    conn = get_connection()
    # Clear existing to avoid duplicates on re-run
    conn.execute("DELETE FROM pain_points")
    conn.commit()
    conn.close()

    for data_point, value, source, date, category, country in PAIN_POINTS:
        insert_pain_point(data_point, value, source, date, category, country)
        count += 1
    print(f"  ✓ {count} pain points seeded")


def seed_sources():
    from config.uk_insurance import SOURCES as UK_SOURCES
    from config.dach_insurance import SOURCES as DACH_SOURCES

    all_sources = UK_SOURCES + DACH_SOURCES + [UK_IMAP_SOURCE]
    print(f"Seeding {len(all_sources)} sources...")

    count = 0
    for s in all_sources:
        upsert_source(
            name=s["name"],
            url=s["url"],
            source_type=s.get("source_type", "rss"),
            tier=s.get("tier", 2),
            categories=s.get("categories", []),
        )
        count += 1
        print(f"  ✓ {s['name']}")

    print(f"  ✓ {count} sources registered")


if __name__ == "__main__":
    print("=== Descartes Content Engine — DB Init ===")
    init_db()
    print("✓ Database tables created")
    seed_pain_points()
    seed_sources()
    print("=== Init complete. Ready to run Monitor agent. ===")
    print("\nNext steps:")
    print("  1. cp .env.example .env")
    print("  2. Add your ANTHROPIC_API_KEY to .env")
    print("  3. python scripts/run_monitor.py")
    print("  4. python scripts/run_analyse.py")
    print("  5. uvicorn api.main:app --port 8000")

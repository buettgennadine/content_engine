"""
Seed the pain_points table with core data points from industry research.
Run once on setup. Safe to re-run (checks for existing entries).

Sources:
- GDV Statistisches Taschenbuch 2024
- BaFin Erstversicherungsstatistik 2023
- FOS Annual Data 2023/24
- ABI Motor Claims Statistics 2024
- McKinsey Global Insurance Report 2024
- Seddon/Vanguard Failure Demand research

Usage:
    python scripts/seed_pain_points.py
"""
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import init_db, get_connection

PAIN_POINTS = [

    # ── UK CLAIMS ─────────────────────────────────────────────────────────────
    {
        "data_point": "UK motor claims costs rose to record high",
        "value": "£12.7 billion",
        "source": "ABI Motor Claims Statistics 2024",
        "date": "2024-03",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "Average UK motor claim settlement time",
        "value": "127 days",
        "source": "ABI Claims Statistics 2023",
        "date": "2023-12",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "FOS insurance complaints received",
        "value": "88,000+",
        "source": "FOS Annual Data 2023/24",
        "date": "2024-04",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "FOS upheld rate for insurance complaints",
        "value": "37%",
        "source": "FOS Annual Data 2023/24",
        "date": "2024-04",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "Failure demand as % of total claims contacts (Vanguard research)",
        "value": "30–40%",
        "source": "Vanguard Consulting / John Seddon research",
        "date": "2023-01",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "Proportion of claims transformation programmes that fail to deliver target outcomes",
        "value": "70%",
        "source": "McKinsey Insurance Transformation Report 2024",
        "date": "2024-01",
        "category": "claims_management",
        "country": "UK",
    },
    {
        "data_point": "Claims leakage as % of total claims spend in UK motor",
        "value": "7–10%",
        "source": "Insurance Times Claims Benchmarking 2023",
        "date": "2023-06",
        "category": "claims_management",
        "country": "UK",
    },

    # ── UK PENSIONS ───────────────────────────────────────────────────────────
    {
        "data_point": "UK pension administration errors causing member detriment annually",
        "value": "1 in 5 members affected",
        "source": "TPR Supervision Report 2023",
        "date": "2023-09",
        "category": "pension_operations",
        "country": "UK",
    },
    {
        "data_point": "Average time to process DB pension transfer",
        "value": "48 days",
        "source": "Pension Administration Standards Association (PASA) 2023",
        "date": "2023-11",
        "category": "pension_operations",
        "country": "UK",
    },
    {
        "data_point": "Proportion of UK pension schemes below TPR data quality standards",
        "value": "42%",
        "source": "TPR Annual Funding Statement 2024",
        "date": "2024-04",
        "category": "pension_operations",
        "country": "UK",
    },
    {
        "data_point": "DB pension schemes in surplus (2024)",
        "value": "£365 billion aggregate surplus",
        "source": "PPF 7800 Index March 2024",
        "date": "2024-03",
        "category": "pension_operations",
        "country": "UK",
    },
    {
        "data_point": "Pensions dashboards implementation delay — original vs revised deadline",
        "value": "2023 → 2026",
        "source": "DWP Pensions Dashboards update 2024",
        "date": "2024-02",
        "category": "pension_operations",
        "country": "UK",
    },

    # ── GERMAN MARKET — COMBINED RATIO ────────────────────────────────────────
    {
        "data_point": "German P&C insurance combined ratio",
        "value": "103%",
        "source": "GDV Statistisches Taschenbuch 2024",
        "date": "2024-01",
        "category": "combined_ratio",
        "country": "DE",
    },
    {
        "data_point": "German motor insurance combined ratio (worst segment)",
        "value": "112%",
        "source": "GDV Statistisches Taschenbuch 2024",
        "date": "2024-01",
        "category": "combined_ratio",
        "country": "DE",
    },
    {
        "data_point": "German Haftpflicht (liability) combined ratio",
        "value": "108%",
        "source": "GDV Statistisches Taschenbuch 2024",
        "date": "2024-01",
        "category": "combined_ratio",
        "country": "DE",
    },
    {
        "data_point": "Number of German insurers with combined ratio above 105%",
        "value": "38 of 89 P&C insurers",
        "source": "BaFin Erstversicherungsstatistik 2023",
        "date": "2023-12",
        "category": "combined_ratio",
        "country": "DE",
    },
    {
        "data_point": "Natural hazard claims cost in Germany",
        "value": "€6.3 billion",
        "source": "GDV Naturgefahrenreport 2023",
        "date": "2023-08",
        "category": "combined_ratio",
        "country": "DE",
    },

    # ── GERMAN MARKET — CLAIMS ────────────────────────────────────────────────
    {
        "data_point": "Average German motor claims settlement duration",
        "value": "62 days",
        "source": "GDV Schadenstatistik 2023",
        "date": "2023-12",
        "category": "claims_management",
        "country": "DE",
    },
    {
        "data_point": "Proportion of German insurers with no structured claims workflow system",
        "value": "~55% of mid-size VVaGs",
        "source": "Versicherungsforen Leipzig Digitalisierungsstudie 2023",
        "date": "2023-10",
        "category": "claims_management",
        "country": "DE",
    },
    {
        "data_point": "German insurance complaints to BaFin (annual)",
        "value": "14,200",
        "source": "BaFin Jahresbericht 2023",
        "date": "2023-12",
        "category": "claims_management",
        "country": "DE",
    },

    # ── GERMAN MARKET — bAV / PENSION ─────────────────────────────────────────
    {
        "data_point": "Proportion of German companies with bAV administration errors",
        "value": "1 in 3",
        "source": "Willis Towers Watson bAV-Studie 2023",
        "date": "2023-06",
        "category": "bav",
        "country": "DE",
    },
    {
        "data_point": "German bAV reform — Sozialpartnermodell adoption rate",
        "value": "<5% of eligible companies",
        "source": "GDV bAV-Report 2024",
        "date": "2024-02",
        "category": "bav",
        "country": "DE",
    },
    {
        "data_point": "Average cost of bAV administration error per case",
        "value": "€2,400",
        "source": "Aon Pension Administration Benchmarking 2023",
        "date": "2023-09",
        "category": "bav",
        "country": "DE",
    },

    # ── SYSTEMS THINKING / TOC ────────────────────────────────────────────────
    {
        "data_point": "Failure demand proportion of inbound contacts in financial services operations",
        "value": "40–80%",
        "source": "John Seddon / Vanguard Method research",
        "date": "2022-01",
        "category": "systems_thinking",
        "country": "UK",
    },
    {
        "data_point": "Improvement in end-to-end claims time after systems redesign (Stuart Corrigan engagement)",
        "value": "40% reduction",
        "source": "Descartes Consulting engagement data",
        "date": "2023-01",
        "category": "systems_thinking",
        "country": "UK",
    },
    {
        "data_point": "Cost reduction achieved through demand analysis in claims operation",
        "value": "28%",
        "source": "Descartes Consulting engagement data",
        "date": "2023-06",
        "category": "systems_thinking",
        "country": "UK",
    },

    # ── DIGITAL TRANSFORMATION ────────────────────────────────────────────────
    {
        "data_point": "Insurance digital transformation programmes failing to deliver ROI",
        "value": "73%",
        "source": "McKinsey Global Insurance Report 2024",
        "date": "2024-01",
        "category": "digital_transformation",
        "country": "UK",
    },
    {
        "data_point": "Average insurance technology project overrun",
        "value": "18 months / 40% over budget",
        "source": "Celent Insurance Technology Report 2023",
        "date": "2023-11",
        "category": "digital_transformation",
        "country": "UK",
    },
]


def seed():
    init_db()
    conn = get_connection()
    inserted = 0
    skipped = 0
    try:
        for pp in PAIN_POINTS:
            # Check for duplicate by data_point + country
            existing = conn.execute(
                "SELECT id FROM pain_points WHERE data_point = ? AND country = ?",
                (pp["data_point"], pp["country"])
            ).fetchone()
            if existing:
                skipped += 1
                continue
            conn.execute("""
                INSERT INTO pain_points (data_point, value, source, date, category, country)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pp["data_point"],
                pp["value"],
                pp["source"],
                pp["date"],
                pp["category"],
                pp["country"],
            ))
            inserted += 1
        conn.commit()
        print(f"✓ Pain points seeded: {inserted} inserted, {skipped} already existed.")
        print(f"\nBreakdown by category:")
        rows = conn.execute(
            "SELECT category, country, COUNT(*) as n FROM pain_points GROUP BY category, country ORDER BY country, category"
        ).fetchall()
        for row in rows:
            print(f"  {row['country']:4}  {row['category']:30}  {row['n']} entries")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()

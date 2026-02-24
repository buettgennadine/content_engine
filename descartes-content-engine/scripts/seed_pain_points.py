#!/usr/bin/env python3
"""Seed the pain_points table with known data from Master SKILL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(override=True)
from core.database import init_db, get_connection

init_db()

PAIN_POINTS = [
    # UK Claims
    {"data_point": "FOS complaints volume", "value": "305,726 (2024/25, +54%)", "source": "FOS Annual Data 2024/25", "date": "2025-07", "category": "claims_management", "country": "UK"},
    {"data_point": "Claims share of GI complaints", "value": "71%", "source": "FOS", "date": "2025-07", "category": "claims_management", "country": "UK"},
    {"data_point": "Motor claims total 2024", "value": "£11.7B record (+17%)", "source": "ABI Statistics 2024", "date": "2024-12", "category": "claims_management", "country": "UK"},
    {"data_point": "Motor average claim Q4 2024", "value": "£5,300", "source": "ABI Statistics 2024", "date": "2024-12", "category": "claims_management", "country": "UK"},
    {"data_point": "Property claims 2025", "value": "£6.1B record", "source": "ABI Statistics 2025", "date": "2025-04", "category": "claims_management", "country": "UK"},
    {"data_point": "GI Combined Ratio 2024", "value": "£1.18 per £1 premium (5th consecutive loss year)", "source": "ABI 2024", "date": "2024-12", "category": "claims_management", "country": "UK"},
    {"data_point": "UK insurers with staff shortages", "value": "72%", "source": "Industry Survey 2024", "date": "2024", "category": "claims_management", "country": "UK"},
    {"data_point": "Legacy IT as digitisation blocker", "value": "9 out of 10 insurers cite it", "source": "Insurtech study 2024", "date": "2024", "category": "claims_technology", "country": "UK"},
    {"data_point": "Storm claims paid in 2024", "value": "Only 32%", "source": "FCA 2024", "date": "2024", "category": "claims_management", "country": "UK"},
    {"data_point": "Claims handler decline forecast", "value": "60% over next decade", "source": "Industry forecast", "date": "2024", "category": "claims_management", "country": "UK"},
    {"data_point": "STP rate — industry vs AI-first", "value": "7% industry vs 57% AI-first insurers", "source": "McKinsey Insurance Report", "date": "2024", "category": "claims_technology", "country": "UK"},
    {"data_point": "Claims leakage", "value": "5-18% (audit avg 11%)", "source": "Claims Audit Data", "date": "2024", "category": "claims_management", "country": "UK"},
    # UK Pensions
    {"data_point": "Pensions Dashboard delay", "value": "2023 → 31 Oct 2026, cost overrun £235m → £289m (+23%)", "source": "DWP 2024", "date": "2024", "category": "pension_operations", "country": "UK"},
    {"data_point": "Pension admins struggling with recruitment", "value": "80%", "source": "Pension Admin Survey 2024", "date": "2024", "category": "pension_operations", "country": "UK"},
    {"data_point": "Regulatory complexity as top-3 challenge", "value": "58% of pension admins", "source": "TPR Survey 2024", "date": "2024", "category": "pension_operations", "country": "UK"},
    # Germany
    {"data_point": "German nat-cat claims growth", "value": "+28% annually (2020-2023)", "source": "GDV Statistisches Taschenbuch 2024", "date": "2024", "category": "claims_management", "country": "DE"},
    {"data_point": "German average motor claim", "value": "~€4,000 (+8.6% YoY)", "source": "GDV 2024", "date": "2024", "category": "claims_management", "country": "DE"},
    {"data_point": "German claims automation range", "value": "4%-40% (leaders: 80% for glass claims)", "source": "McKinsey DE Insurance 2024", "date": "2024", "category": "claims_technology", "country": "DE"},
    {"data_point": "bAV too complex for companies", "value": "50% of companies", "source": "bAV-Studie 2024", "date": "2024", "category": "pension_operations", "country": "DE"},
    {"data_point": "German insurers planning digitisation without systems thinking", "value": "62%", "source": "Versicherungsforen Leipzig 2024", "date": "2024", "category": "digital_transformation", "country": "DE"},
    # Systems Thinking
    {"data_point": "Failure Demand in service organisations", "value": "40-60% (Seddon/Vanguard)", "source": "Vanguard Method Research", "date": "2023", "category": "systems_thinking", "country": "UK"},
    {"data_point": "Failure Demand extreme case", "value": "70% failure demand, 2.5 transactions per customer", "source": "Vanguard case study", "date": "2023", "category": "systems_thinking", "country": "UK"},
    {"data_point": "After systems redesign — headcount", "value": "700 → 300 staff, work returned from India to UK", "source": "Vanguard/Descartes case study", "date": "2023", "category": "systems_thinking", "country": "UK"},
]

conn = get_connection()
try:
    for pp in PAIN_POINTS:
        conn.execute("""
            INSERT OR IGNORE INTO pain_points (data_point, value, source, date, category, country)
            VALUES (?,?,?,?,?,?)
        """, (pp["data_point"], pp["value"], pp["source"], pp["date"], pp["category"], pp["country"]))
    conn.commit()
    print(f"Seeded {len(PAIN_POINTS)} pain points.")
finally:
    conn.close()

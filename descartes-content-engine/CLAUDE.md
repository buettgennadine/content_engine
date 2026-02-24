# Descartes Content Engine — CLAUDE.md

## System Overview

Agentic AI content pipeline for Stuart Corrigan / Descartes Consulting Ltd.
Automates LinkedIn thought leadership content for UK and DACH insurance markets.

## Architecture

```
Python Backend (this repo)
  → SQLite (data/content_engine.db)
  → FastAPI Layer (to build: /api/*)
  → HTML Frontend (to build: cream/copper/navy theme)
```

## Run Commands

```bash
python scripts/run_monitor.py --config uk_insurance
python scripts/run_analyse.py --config uk_insurance
python scripts/run_ideate.py
python scripts/run_drafts.py
python scripts/run_briefing.py
```

## Cron Schedule

```
0 */6 * * *  python scripts/run_monitor.py --config uk_insurance
0 18 * * *   python scripts/run_analyse.py --config uk_insurance
0 20 * * 0   python scripts/run_ideate.py
0 6  * * 1   python scripts/run_drafts.py
0 15 * * 5   python scripts/run_briefing.py
```

## Key Rules

1. VPS Threshold: Only VPS > 60 enters drafting queue
2. British English throughout
3. Anti-Language: NO "transformation journey", "stakeholder buy-in", "leverage", "synergies"
4. Attribution: NEVER blame individuals — system design causes outcomes
5. Allianz is NOT a possible client

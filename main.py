#!/usr/bin/env python3
"""
UNH Research Agent — entry point.

Monitors Medicare/Medicaid regulatory changes, CMS announcements, and competitor
activity relevant to UnitedHealth Group (UNH), then sends a ≤100-word daily
email brief.

Usage
-----
Run once (now):
    python main.py

Run on a daily schedule (8 AM by default):
    python main.py --schedule
    python main.py --schedule --time 07:30

Smoke-test email formatting with mock data:
    python main.py --test-email

Override the default lookback window:
    python main.py --lookback-days 3
"""

import argparse
import logging
import sys
import time
from datetime import datetime

import schedule

import config
from agent.database import save_daily_record
from agent.emailer import generate_digest, send_digest
from agent.researcher import run_research
from agent.state import filter_new_findings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("unh-agent")


def run_daily_job() -> None:
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("UNH Research Agent — daily job started %s", start.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    try:
        logger.info("Phase 1/3 — Running competitive & regulatory intelligence research …")
        raw_findings = run_research()
        if not raw_findings:
            logger.info("No findings returned from research phase.")

        logger.info("Phase 2/3 — Deduplicating against previously sent items …")
        new_findings = filter_new_findings(raw_findings)

        logger.info("Phase 3/3 — Generating digest and sending email …")
        digest_text = generate_digest(new_findings)
        send_digest(new_findings, digest_text)

        logger.info("Phase 4/4 — Saving record to database …")
        save_daily_record(new_findings, digest_text)

        elapsed = (datetime.now() - start).total_seconds()
        logger.info("Job complete in %.1f s | %d new finding(s) in digest", elapsed, len(new_findings))

    except KeyboardInterrupt:
        raise
    except Exception:
        logger.exception("Job failed with unhandled exception")
        raise


_MOCK_FINDINGS = [
    {
        "company": "CMS",
        "type": "rate_notice",
        "relevance": "HIGH",
        "vc_firm": "N/A",
        "description": (
            "CMS releases 2026 Medicare Advantage preliminary rate notice with +3.7% benchmark "
            "increase; lower than industry expected, pressuring MA plan margins across all carriers."
        ),
        "source": "https://cms.gov/medicare/health-plans/medicareadvtgspecratestats",
        "found_at": datetime.now().isoformat(),
    },
    {
        "company": "Humana",
        "type": "competitor_news",
        "relevance": "HIGH",
        "vc_firm": "N/A",
        "description": (
            "Humana exits 13 Medicare Advantage markets for 2026, citing medical cost pressures; "
            "approximately 560,000 members must select new plans — potential UNH enrollment opportunity."
        ),
        "source": "https://humana.com/newsroom/ma-market-exit",
        "found_at": datetime.now().isoformat(),
    },
    {
        "company": "Elevance Health",
        "type": "earnings",
        "relevance": "MEDIUM",
        "vc_firm": "N/A",
        "description": (
            "Elevance Q1 2026 earnings: MA MLR rose to 89.2% vs 86.1% prior year; "
            "management cites higher-than-expected inpatient utilization in dual-eligible population."
        ),
        "source": "https://elevancehealth.com/investors/q1-2026-earnings",
        "found_at": datetime.now().isoformat(),
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="UNH Competitive & Regulatory Intelligence Agent")
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--time", default="08:00", metavar="HH:MM")
    parser.add_argument("--test-email", action="store_true")
    parser.add_argument("--lookback-days", type=int, default=None)
    args = parser.parse_args()

    config.validate()

    if args.lookback_days is not None:
        config.LOOKBACK_DAYS = args.lookback_days

    if args.test_email:
        logger.info("TEST-EMAIL mode — sending mock digest (no live research)")
        send_digest(_MOCK_FINDINGS)
        return

    if args.schedule:
        schedule.every().day.at(args.time).do(run_daily_job)
        run_daily_job()
        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        run_daily_job()


if __name__ == "__main__":
    main()

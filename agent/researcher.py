"""
Research engine: breaks the daily scan into 3 focused search blocks that run
sequentially, avoiding rate-limit errors caused by one massive API call.

Each block uses claude-sonnet-4-6 with a short, targeted prompt.
A 15-second pause between blocks keeps token-per-minute usage well within
Anthropic's standard rate limits.

Focus areas:
  1. Direct competitor news (CVS/Aetna, Elevance, Centene, Humana, Privia, BCBS)
  2. CMS / Medicare regulations, rate notices, and Chris Klomp statements
  3. Broader managed care market signals
"""

import logging
import time
from datetime import datetime, timedelta

import anthropic

import config
from data.competitors import (
    DIRECT_COMPETITOR_NAMES,
    REGULATORY_KEYWORDS,
)

logger = logging.getLogger(__name__)

# ── Compact system prompt ─────────────────────────────────────────────────────

_SEARCH_SYSTEM = """\
You are a competitive and regulatory intelligence analyst for UnitedHealth Group (UNH), \
the largest U.S. health insurer and managed care company (UnitedHealthcare + Optum).

DIRECT competitors: CVS Health/Aetna, Elevance Health (Anthem), Centene, Humana, \
Privia Health, Blue Cross Blue Shield (BCBS), Molina Healthcare, Kaiser Permanente.

KEY REGULATORY FOCUS: CMS (Centers for Medicare & Medicaid Services) — Medicare Advantage \
rate notices, final rules, Star Ratings, RADV audits, prior authorization rules, Medicaid \
managed care. Also monitor Chris Klomp (CMS Medicare Administrator) for any public statements.

For each finding, output one line in this EXACT format (pipe-delimited):
FINDING|||[Company or Agency]|||[competitor_news|cms_regulation|rate_notice|star_ratings|ma_policy|medicaid|market_signal|earnings]|||[HIGH|MEDIUM]|||[Source or N/A]|||[One sentence with key detail: policy change, $ impact, enrollment figure, quote, etc.]|||[Source URL]

HIGH relevance: CMS rate notice or final rule with material MA financial impact; Chris Klomp public statement on Medicare policy; \
direct competitor announces major MA expansion/exit or strategic shift; antitrust/regulatory action against managed care; \
Star Ratings change affecting MA bonus payments; large employer or government contract switches managed care plan.
MEDIUM relevance: competitor earnings showing notable MA enrollment change or MLR shift; state Medicaid contract award/loss; \
value-based care company raises significant funding competing with Optum; CMS proposes new MA audit or compliance rule.
Do NOT output LOW relevance findings.
When done searching, output: BLOCK_COMPLETE
"""

# ── Three focused search blocks ───────────────────────────────────────────────

def _date_range() -> str:
    today    = datetime.now()
    week_ago = today - timedelta(days=7)
    return f"{week_ago.strftime('%B %d')}–{today.strftime('%B %d, %Y')}"


_SEARCH_BLOCKS = [
    {
        "name": "competitor_news",
        "prompt_template": """\
Search for news from the past 7 days ({date_range}) about these \
UnitedHealth Group direct competitors:

• CVS Health / Aetna — Medicare Advantage strategy, earnings, enrollment changes, PBM news, MinuteClinic/Oak Street expansion
• Elevance Health (Anthem) — Medicare Advantage, Medicaid, earnings, acquisitions, care delivery expansion
• Centene Corporation — Medicaid contract wins/losses, Medicare Advantage growth, state contract news
• Humana — Medicare Advantage enrollment, CenterWell primary care, earnings, strategic announcements
• Privia Health — value-based care expansion, physician group acquisitions, Optum competition
• Blue Cross Blue Shield (BCBS) / HCSC — Medicare Advantage market moves, employer contract news, M&A

Search each company + "Medicare Advantage" OR "earnings" OR "announcement" OR "enrollment" 2025 2026.
Output all HIGH and MEDIUM relevance FINDING||| lines, then: BLOCK_COMPLETE""",
    },
    {
        "name": "cms_medicare_regulations",
        "prompt_template": """\
Search for news and announcements from the past 7 days ({date_range}) about:

PART A — CMS Medicare and Medicaid policy:
• CMS Medicare Advantage rate notice OR final rule 2025 2026 — any new announcements, proposed rules, or finalized rates
• CMS Star Ratings update — any new releases, methodology changes, or appeals news
• CMS RADV audit — risk adjustment data validation settlements, new rules, or industry response
• CMS prior authorization rule — Medicare Advantage prior auth requirements, implementation updates
• CMS ACO REACH OR value-based care model — new model launches, changes, or participant updates
• Medicaid managed care — rate-setting, contract awards, state waivers, redeterminations
• Medicare Part D — premium changes, benefit redesign, IRA implementation updates

PART B — Chris Klomp specifically:
• Search: "Chris Klomp" — any LinkedIn posts, speeches, congressional testimony, interviews, or public statements
• Search: "Chris Klomp CMS" OR "Chris Klomp Medicare" 2025 2026
• Search: CMS Medicare administrator statement OR announcement {month_year}

Output all HIGH and MEDIUM relevance FINDING||| lines, then: BLOCK_COMPLETE""",
    },
    {
        "name": "market_signals",
        "prompt_template": """\
Search for news from the past 7 days ({date_range}) about broader managed care \
and health insurance market signals relevant to UnitedHealth Group:

• Medicare Advantage "enrollment" OR "market share" OR "exit" OR "expansion" 2026
• health insurer "medical loss ratio" OR "MLR" deterioration OR improvement 2026
• managed care "antitrust" OR "DOJ" OR "FTC" OR "vertical integration" 2026
• "switching from UnitedHealthcare" OR "leaving UnitedHealthcare" employer contract 2026
• Optum competitor announcement OR "value-based care" acquisition {month_year}
• health plan "prior authorization" legislation OR regulation 2026
• Medicare Advantage "overpayment" OR "upcoding" OR "risk adjustment" investigation 2026
• managed care earnings "guidance" OR "outlook" OR "cost trend" 2026

Also search:
• Oscar Health OR Clover Health OR Bright Health — Medicare Advantage news, funding, market moves
• Amazon health OR One Medical OR Walmart Health — employer benefits or primary care expansion competing with Optum

Output all HIGH and MEDIUM relevance FINDING||| lines, then: BLOCK_COMPLETE""",
    },
]


# ── Parsing ───────────────────────────────────────────────────────────────────

def _parse_findings(text: str) -> list[dict]:
    findings = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("FINDING|||"):
            continue
        parts = line.split("|||")
        if len(parts) < 7:
            logger.warning("Skipping malformed finding: %s", line[:100])
            continue
        findings.append({
            "company":     parts[1].strip(),
            "type":        parts[2].strip().lower(),
            "relevance":   parts[3].strip().upper(),
            "vc_firm":     parts[4].strip(),
            "description": parts[5].strip(),
            "source":      parts[6].strip(),
            "found_at":    datetime.now().isoformat(),
        })
    return findings


# ── Single block runner ───────────────────────────────────────────────────────

def _run_block(client: anthropic.Anthropic, block: dict) -> list[dict]:
    """Run one focused search block. Returns findings (empty list on failure)."""
    date_range  = _date_range()
    month_year  = datetime.now().strftime("%B %Y")
    user_prompt = block["prompt_template"].format(
        date_range=date_range,
        month_year=month_year,
    )

    messages       = [{"role": "user", "content": user_prompt}]
    accumulated    = ""
    continuations  = 0
    max_cont       = 3

    while continuations <= max_cont:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=_SEARCH_SYSTEM,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=messages,
        )

        for content_block in response.content:
            if hasattr(content_block, "text"):
                accumulated += content_block.text + "\n"

        if response.stop_reason == "end_turn":
            break
        elif response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continuations += 1
            logger.debug("Block '%s' pause_turn %d/%d", block["name"], continuations, max_cont)
        else:
            logger.warning("Block '%s' unexpected stop_reason=%s", block["name"], response.stop_reason)
            break

    return _parse_findings(accumulated)


# ── Main entry point ──────────────────────────────────────────────────────────

BLOCK_PAUSE_SECONDS = 15


def run_research() -> list[dict]:
    """
    Run daily research across 3 sequential focused search blocks.
    """
    client = anthropic.Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
        timeout=180.0,
    )

    all_findings: list[dict] = []

    for i, block in enumerate(_SEARCH_BLOCKS):
        logger.info(
            "Search block %d/%d — %s", i + 1, len(_SEARCH_BLOCKS), block["name"]
        )
        try:
            findings = _run_block(client, block)
            all_findings.extend(findings)
            logger.info("  → %d finding(s)", len(findings))
        except anthropic.RateLimitError:
            logger.warning(
                "Block '%s' hit rate limit — waiting 60 s then skipping.",
                block["name"],
            )
            time.sleep(60)
        except Exception as exc:
            logger.error(
                "Block '%s' failed (%s) — continuing with remaining blocks.",
                block["name"], exc,
            )

        if i < len(_SEARCH_BLOCKS) - 1:
            logger.debug("Pausing %d s before next block …", BLOCK_PAUSE_SECONDS)
            time.sleep(BLOCK_PAUSE_SECONDS)

    seen:    set[str]  = set()
    deduped: list[dict] = []
    for f in all_findings:
        key = f"{f['company'].lower()}|{f['type'].lower()}"
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    deduped.sort(key=lambda f: (0 if f.get("relevance") == "HIGH" else 1))

    logger.info(
        "Research complete — %d unique findings (%d HIGH, %d MEDIUM) across %d blocks",
        len(deduped),
        sum(1 for f in deduped if f.get("relevance") == "HIGH"),
        sum(1 for f in deduped if f.get("relevance") == "MEDIUM"),
        len(_SEARCH_BLOCKS),
    )
    return deduped

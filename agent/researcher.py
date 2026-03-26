"""
Research engine: breaks the daily scan into 3 focused search blocks that run
sequentially, avoiding rate-limit errors caused by one massive API call.

Each block uses claude-sonnet-4-6 (cheaper, same search quality) with a
short, targeted prompt. A 15-second pause between blocks keeps token-per-
minute usage well within Anthropic's standard rate limits.

claude-opus-4-6 is NOT used here — only in emailer.py for the final digest.
"""

import logging
import time
from datetime import datetime, timedelta

import anthropic

import config
from data.competitors import (
    COMPETITOR_DOMAIN_KEYWORDS,
    DIRECT_COMPETITOR_NAMES,
    INDIRECT_COMPETITOR_NAMES,
)

logger = logging.getLogger(__name__)

# ── Compact system prompt (sent with every search block) ─────────────────────
# Kept short on purpose — the full competitor context is NOT needed here.
# Each block prompt carries its own specific instructions.

_SEARCH_SYSTEM = """\
You are a competitive intelligence analyst for Guidewire Software (GWRE), \
the #1 P&C insurance core system (policy admin, billing, claims).

DIRECT competitors: Duck Creek Technologies, Majesco, Sapiens International, \
Insurity, OneShield, EIS Group, Socotra, Instanda, FINEOS, Applied Systems.

INDIRECT competitors (AI point solutions expanding into core territory): \
Shift Technology, Gradient AI, Snapsheet, Five Sigma, CLARA Analytics, \
Tractable, Betterview, Cape Analytics, CCC Intelligent Solutions.

For each finding, output one line in this EXACT format (pipe-delimited):
FINDING|||[Company]|||[investment|product|metrics|partnership|platform_shift|vc_signal]|||[HIGH|MEDIUM]|||[VC firm or N/A]|||[One sentence with key detail: $amount, product name, carrier name, etc.]|||[Source URL]

HIGH relevance: direct competitor funding/product/customer win; carrier leaving Guidewire; \
AI tool expanding into full platform.
MEDIUM relevance: insurtech Series B+ for claims/policy/billing; VC blog about core-system disruption.
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
        "name": "direct_competitors",
        "prompt_template": """\
Search for news from the past 7 days ({date_range}) about these \
Guidewire direct competitors:

• Duck Creek Technologies — product news, funding, customer wins
• Majesco (MJCO) — earnings, new releases, customer announcements
• Sapiens International (SPNS) — M&A, product, customer news
• Insurity — funding, product, partnerships
• OneShield / EIS Group — new deals or product launches
• Socotra — funding rounds, new carrier customers, product updates
• Instanda — funding, growth metrics, new markets

Search for each company name + "news" or "announcement" or "funding" 2025 2026.
Output all HIGH and MEDIUM relevance FINDING||| lines you find, then: BLOCK_COMPLETE""",
    },
    {
        "name": "ai_insurtech_and_vc",
        "prompt_template": """\
Search for news from the past 7 days ({date_range}) about:

PART A — AI insurance companies expanding into core-system territory:
• Shift Technology — new deals, funding, product expansion
• Gradient AI — funding, underwriting/claims product news
• Snapsheet, Five Sigma, CLARA Analytics — funding or product launches
• Tractable, Betterview, Cape Analytics — new partnerships or funding

PART B — VC portfolio announcements in insurance tech:
• Search: "Anthemis" OR "QED Investors" OR "Munich Re Ventures" insurance investment 2026
• Search: "Nationwide Ventures" OR "XL Innovate" OR "Aquiline" insurtech portfolio news
• Search: "Insight Partners" OR "TCV" OR "General Catalyst" insurance software investment 2026
• Search: Ribbit Capital OR Mundi Ventures insurtech 2026

Output all HIGH and MEDIUM relevance FINDING||| lines, then: BLOCK_COMPLETE""",
    },
    {
        "name": "market_signals",
        "prompt_template": """\
Search for news from the past 7 days ({date_range}) about broader \
P&C insurance technology market signals:

• insurtech funding round Series B C D 2026 "policy administration" OR "claims management" OR "billing"
• insurance carrier "replaced" OR "migrated" OR "switched from" Guidewire
• new P&C insurance platform startup raised funding 2026
• Guidewire competitor announcement {month_year}
• VC partner blog post insurtech investment thesis 2026

Also search for any of these lesser-covered names with recent news:
Unqork insurance, Appian insurance platform, Lemonade technology platform, \
Kin Insurance platform, CCC Intelligent Solutions news.

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
            model="claude-sonnet-4-6",   # cheaper than Opus; same search quality
            max_tokens=3000,             # sufficient for focused block output
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

BLOCK_PAUSE_SECONDS = 15   # pause between blocks to stay within rate limits


def run_research() -> list[dict]:
    """
    Run daily research across 3 sequential focused search blocks.

    Using claude-sonnet-4-6 per block keeps each call small enough to
    avoid rate-limit errors. Blocks run sequentially with a 15-second
    pause between them.
    """
    client = anthropic.Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
        timeout=180.0,   # 3-minute timeout per block
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

        # Pause between blocks (skip after the last one)
        if i < len(_SEARCH_BLOCKS) - 1:
            logger.debug("Pausing %d s before next block …", BLOCK_PAUSE_SECONDS)
            time.sleep(BLOCK_PAUSE_SECONDS)

    # Deduplicate within this run (same company+type from multiple blocks)
    seen:   set[str]   = set()
    deduped: list[dict] = []
    for f in all_findings:
        key = f"{f['company'].lower()}|{f['type'].lower()}"
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    # HIGH findings first
    deduped.sort(key=lambda f: (0 if f.get("relevance") == "HIGH" else 1))

    logger.info(
        "Research complete — %d unique findings (%d HIGH, %d MEDIUM) across %d blocks",
        len(deduped),
        sum(1 for f in deduped if f.get("relevance") == "HIGH"),
        sum(1 for f in deduped if f.get("relevance") == "MEDIUM"),
        len(_SEARCH_BLOCKS),
    )
    return deduped

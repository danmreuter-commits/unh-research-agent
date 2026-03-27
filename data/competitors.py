"""UnitedHealth Group (UNH) competitive landscape and regulatory intelligence knowledge base."""

UNH_CONTEXT = """
ABOUT UNITEDHEALTH GROUP (UNH):
UnitedHealth Group is the largest U.S. health insurance and managed care company by revenue and membership.

CORE BUSINESS SEGMENTS:
- UnitedHealthcare: Health benefits — employer-sponsored, Medicare Advantage (MA), Medicaid managed care, individual/exchange plans
- Optum: Health services — OptumHealth (care delivery), OptumInsight (data/analytics/technology), OptumRx (pharmacy benefit management)
TARGET CUSTOMERS: Employers, Medicare/Medicaid beneficiaries, government programs, individual members
BUSINESS MODEL: Premium revenue + fee-based health services; vertically integrated across insurance and care delivery
MARKET POSITION: Largest U.S. health insurer by membership; largest Medicare Advantage plan; largest PBM through OptumRx

---

DIRECT COMPETITORS — health insurance and managed care:
- CVS Health / Aetna: Full-stack managed care + pharmacy (CVS/Caremark PBM + MinuteClinic + Aetna insurance)
- Elevance Health (formerly Anthem): Second-largest U.S. health insurer; Blue Cross Blue Shield licensee; strong Medicare and Medicaid
- Centene Corporation: Largest Medicaid managed care organization; growing Medicare Advantage footprint
- Humana: Medicare-focused insurer; primary care delivery (CenterWell); strong Medicare Advantage market share
- Privia Health: Physician enablement and value-based care organization; competes with Optum care delivery
- Blue Cross Blue Shield (BCBS): National federation of 35+ local plans; largest collective enrollment; major MA competitor in every market
- Molina Healthcare: Medicaid and Medicare-focused managed care; state government contracts
- Kaiser Permanente: Integrated health system; largest nonprofit MA plan
- Health Care Service Corporation (HCSC): BCBS licensee in 5 states; major employer and MA competitor

INDIRECT COMPETITORS — adjacent health services expanding into UNH territory:
- Amazon / One Medical: Primary care delivery + pharmacy (Amazon Pharmacy); expanding into employer health benefits
- Walmart Health: Retail health clinics and primary care; employer health benefit partnerships
- Oscar Health: Tech-forward individual and small group insurance; expanding into MA
- Clover Health: Medicare Advantage with AI-driven care management
- Bright Health: Medicare Advantage (restructuring/wind-down monitoring)

---

REGULATORY INTELLIGENCE — highest priority monitoring:
CMS (Centers for Medicare & Medicaid Services):
- Medicare Advantage rate notices and final rules (Annual Rate Announcement — typically February/April)
- Medicare Part D premium and benefit changes
- Star Ratings updates (October release; directly tied to MA bonus payments)
- RADV (Risk Adjustment Data Validation) audit rules and settlements
- Prior authorization rule changes (MA plans)
- ACO REACH and value-based care program updates
- Medicaid managed care rate-setting, contract awards, and redeterminations
- CMS Innovation Center (CMMI) model launches and changes

KEY CMS OFFICIALS TO MONITOR:
- Chris Klomp: Administrator overseeing Medicare at CMS; any public statements, testimony, speeches, LinkedIn posts, or interviews
- CMS Administrator: Overall CMS policy direction
- CMMI Director: Value-based care model announcements

---

WHAT MAKES A FINDING RELEVANT TO UNH:
HIGH relevance:
- CMS issues Medicare Advantage rate notice, final rule, or policy change with material financial impact
- Chris Klomp makes public statement or post about Medicare, MA rates, or CMS policy direction
- Direct competitor (CVS/Aetna, Elevance, Centene, Humana) announces major MA expansion, exit, or strategic shift
- Large employer or government entity switches MA or managed care contracts away from UNH to a competitor
- DOJ/FTC antitrust action related to health insurance, PBM, or vertical integration
- CMS Star Ratings change materially affecting MA bonus payments
- Congressional or regulatory action threatening MA reimbursement rates or plan requirements

MEDIUM relevance:
- Competitor reports earnings with notable MA enrollment gain/loss or MLR deterioration
- State Medicaid contract award or loss for a direct competitor
- Employer benefits consultant publishes analysis on managed care market shifts
- Value-based care or care delivery company raises significant funding competing with Optum
- CMS proposes new audit, compliance, or reporting requirement for MA plans

LOW relevance (exclude):
- Small regional health plans with no national MA or Medicaid overlap
- Hospital/health system news unrelated to managed care or value-based contracting
- Pre-seed/seed health IT rounds under $10M with no managed care angle
- Pure dental, vision, or supplemental insurance with no MA overlap
"""

DIRECT_COMPETITOR_NAMES = [
    "cvs health", "aetna", "elevance health", "anthem", "centene",
    "humana", "privia health", "blue cross blue shield", "bcbs",
    "molina healthcare", "kaiser permanente", "hcsc",
]

INDIRECT_COMPETITOR_NAMES = [
    "amazon health", "one medical", "walmart health", "oscar health",
    "clover health", "bright health",
]

REGULATORY_KEYWORDS = [
    "medicare advantage", "medicare part d", "CMS rate notice", "final rule",
    "star ratings", "RADV", "risk adjustment", "prior authorization",
    "ACO REACH", "CMMI", "medicaid managed care", "value-based care",
    "medical loss ratio", "MLR", "MA rate announcement", "Chris Klomp",
    "managed care", "health plan enrollment", "PBM regulation",
]

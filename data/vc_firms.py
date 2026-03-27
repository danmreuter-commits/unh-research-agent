"""Healthcare-focused investors to monitor for managed care and health services investments."""

VC_FIRMS = [
    # Healthcare-focused PE and growth equity
    {"name": "General Atlantic",         "website": "generalatlantic.com",     "blog": None, "healthcare_focus": True},
    {"name": "Warburg Pincus",           "website": "warburgpincus.com",        "blog": None, "healthcare_focus": True},
    {"name": "Welsh Carson",             "website": "welshcarson.com",          "blog": None, "healthcare_focus": True},
    {"name": "Oak HC/FT",                "website": "oakhcft.com",             "blog": "https://www.oakhcft.com/insights/", "healthcare_focus": True},
    {"name": "Andreessen Horowitz Bio",  "website": "a16z.com/bio",            "blog": "https://a16z.com/bio/", "healthcare_focus": True},
    {"name": "General Catalyst Health",  "website": "generalcatalyst.com",     "blog": None, "healthcare_focus": True},
    {"name": "Bessemer Venture Partners","website": "bvp.com",                 "blog": "https://www.bvp.com/blog/", "healthcare_focus": False},
    {"name": "Insight Partners",         "website": "insightpartners.com",     "blog": "https://www.insightpartners.com/ideas/", "healthcare_focus": False},
    {"name": "New Enterprise Associates","website": "nea.com",                 "blog": "https://www.nea.com/blog/", "healthcare_focus": True},
    {"name": "Optum Ventures",           "website": "optumventures.com",       "blog": None, "healthcare_focus": True},
]

VC_NAMES = [f["name"] for f in VC_FIRMS]
HEALTHCARE_FOCUSED_VCS = [f["name"] for f in VC_FIRMS if f["healthcare_focus"]]

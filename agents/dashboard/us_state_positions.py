"""Approximate US state centroid positions for the Recall Radar panel — percentages of
the panel's width/height on a stylized (not geographically precise) map, matching the
original mockup's approach. docs/PLAN.md already scopes this as "approximate via state
centroids, doesn't need to be precise" — this is a simplified grid, not a real
projection. Alaska/Hawaii are placed as insets, not to true geographic scale, which is
standard practice for this kind of stylized US map.
"""

STATE_POSITIONS = {
    "WA": (15, 10), "OR": (12, 20), "CA": (10, 45), "NV": (18, 35), "ID": (22, 20),
    "MT": (30, 12), "WY": (30, 28), "UT": (22, 40), "AZ": (20, 55), "CO": (32, 38),
    "NM": (28, 55), "ND": (40, 10), "SD": (40, 22), "NE": (42, 32), "KS": (44, 42),
    "OK": (46, 52), "TX": (42, 68), "MN": (48, 12), "IA": (50, 25), "MO": (52, 38),
    "AR": (52, 52), "LA": (52, 68), "WI": (54, 16), "IL": (56, 28), "MS": (56, 60),
    "MI": (60, 15), "IN": (60, 30), "KY": (60, 42), "TN": (60, 50), "AL": (60, 60),
    "OH": (65, 28), "WV": (66, 38), "GA": (65, 60), "FL": (68, 80), "SC": (68, 55),
    "NC": (70, 48), "VA": (70, 40), "PA": (72, 25), "NY": (74, 15), "VT": (76, 10),
    "NH": (78, 10), "ME": (80, 5), "MA": (78, 18), "RI": (79, 20), "CT": (77, 22),
    "NJ": (74, 28), "DE": (73, 32), "MD": (72, 35), "DC": (72, 36),
    "AK": (8, 85), "HI": (15, 88),
}


def positions_for_states(state_names: list[str]) -> list[dict]:
    """state_names: free-text-ish state values from recall data (e.g. "MD", "Nationwide",
    "The recalled product was distributed to..."). Anything that isn't a recognized
    2-letter code is skipped — better to show fewer accurate pings than a wrong one."""
    pings = []
    for raw in state_names:
        code = raw.strip().upper()
        if code in STATE_POSITIONS:
            x, y = STATE_POSITIONS[code]
            pings.append({"state": code, "x": x, "y": y})
    return pings

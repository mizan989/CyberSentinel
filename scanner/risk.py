"""
CyberSentinel - Risk Scoring
-------------------------------
Converts a list of vulnerability findings into a single 0-100 risk
score and a human-readable risk level.
"""

SEVERITY_WEIGHTS = {
    "Critical": 40,
    "High": 20,
    "Medium": 10,
    "Low": 4,
    "Informational": 1,
}


def calculate_risk(vulnerabilities):
    if not vulnerabilities:
        return 0.0, "Informational"

    score = 0
    for v in vulnerabilities:
        score += SEVERITY_WEIGHTS.get(v.get("severity"), 0)

    score = min(score, 100)

    if score >= 70:
        level = "Critical"
    elif score >= 40:
        level = "High"
    elif score >= 20:
        level = "Medium"
    elif score > 0:
        level = "Low"
    else:
        level = "Informational"

    return float(score), level

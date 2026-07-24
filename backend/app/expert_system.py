"""
expert_system.py — rule-based dengue triage, forward chaining, from scratch.

Independently re-implemented for this API (see graph_data.py docstring for why).
Rules, conflict-resolution strategies, and the halt-on-goal design are identical
to the verified notebook implementation — including the "derive before you
conclude" fix for the safety-first strategy (see the notebook for the bug story;
this file ships the FIXED, correct version only).
"""
from dataclasses import dataclass, field
from typing import Dict, List


def combine_cf(cf1: float, cf2: float) -> float:
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2)))


@dataclass
class Rule:
    rule_id: str
    conditions: List[str]
    conclusion: str
    cf: float
    rationale: str

    @property
    def specificity(self) -> int:
        return len(self.conditions)

    def applicable(self, facts: Dict[str, float]) -> bool:
        return all(c in facts for c in self.conditions)


@dataclass
class FiredRule:
    rule_id: str
    conditions_met: List[str]
    conclusion: str
    cf: float
    rationale: str
    iteration: int


@dataclass
class TriageResult:
    recommendation: str
    certainty: float
    trace: List[FiredRule] = field(default_factory=list)
    derived_facts: Dict[str, float] = field(default_factory=dict)
    iterations: int = 0
    conflict_strategy: str = ""


RULE_BASE: List[Rule] = [
    Rule("R01", ["fever", "fever_days_2_7"], "probable_dengue_window", 0.70,
         "Acute fever of 2-7 days is the classic dengue presentation window (NDCU case definition)."),
    Rule("R02", ["fever", "headache", "retro_orbital_pain"], "dengue_symptom_cluster", 0.65,
         "Fever with headache and retro-orbital pain is a characteristic dengue symptom cluster."),
    Rule("R03", ["fever", "myalgia", "arthralgia"], "dengue_symptom_cluster", 0.60,
         "Severe muscle and joint pain ('breakbone fever') is highly suggestive of dengue."),
    Rule("R04", ["probable_dengue_window", "dengue_symptom_cluster"], "suspected_dengue", 0.80,
         "Symptom cluster within the febrile window together indicate suspected dengue."),
    Rule("R05", ["fever", "abdominal_pain"], "warning_sign", 0.75,
         "WHO warning sign: severe abdominal pain or tenderness signals plasma leakage risk."),
    Rule("R06", ["fever", "persistent_vomiting"], "warning_sign", 0.75,
         "WHO warning sign: persistent vomiting risks dehydration and impedes oral rehydration."),
    Rule("R07", ["fever", "mucosal_bleeding"], "warning_sign", 0.85,
         "WHO warning sign: mucosal bleeding indicates haemostatic compromise."),
    Rule("R08", ["fever", "lethargy_restlessness"], "warning_sign", 0.80,
         "WHO warning sign: lethargy or restlessness can herald decompensated shock."),
    Rule("R09", ["fever", "fluid_accumulation"], "warning_sign", 0.80,
         "WHO warning sign: clinical fluid accumulation indicates plasma leakage."),
    Rule("R10", ["platelet_drop", "haematocrit_rise"], "plasma_leakage_risk", 0.90,
         "Rising haematocrit with falling platelets is the laboratory signature of plasma leakage."),
    Rule("R11", ["fever", "liver_enlargement"], "warning_sign", 0.70,
         "WHO warning sign: hepatomegaly greater than 2 cm."),
    Rule("R12", ["plasma_leakage_risk"], "REFER_URGENT", 0.90,
         "Laboratory evidence of plasma leakage requires immediate hospital referral."),
    Rule("R13", ["warning_sign", "high_risk_group"], "REFER_URGENT", 0.85,
         "A warning sign in a high-risk patient demands urgent referral."),
    Rule("R14", ["warning_sign"], "REFER", 0.75,
         "Any WHO warning sign warrants hospital referral for observation."),
    Rule("R15", ["suspected_dengue"], "MONITOR", 0.60,
         "Suspected dengue with no warning signs: monitor with daily review and fluid advice."),
    Rule("R16", ["fever"], "HOME_CARE", 0.30,
         "Undifferentiated fever with no dengue indicators: symptomatic home care and safety-netting."),
]

URGENCY = {"REFER_URGENT": 4, "REFER": 3, "MONITOR": 2, "HOME_CARE": 1}
RECOMMENDATIONS = set(URGENCY)

OBSERVABLE_FEATURES = [
    "fever", "fever_days_2_7", "headache", "retro_orbital_pain",
    "myalgia", "arthralgia", "rash",
    "abdominal_pain", "persistent_vomiting", "mucosal_bleeding",
    "lethargy_restlessness", "fluid_accumulation", "liver_enlargement",
    "platelet_drop", "haematocrit_rise", "high_risk_group",
]


def resolve_highest_cf(candidates):
    return sorted(candidates, key=lambda r: -r.cf)


def resolve_most_specific(candidates):
    return sorted(candidates, key=lambda r: (-r.specificity, -r.cf))


def resolve_safety_first(candidates):
    """Derive before you conclude, then most urgent, then most certain. See notebook
    for the bug this design fixes (an earlier version concluded before reasoning,
    producing 126/200 under-referrals)."""
    def key(r):
        is_rec = r.conclusion in RECOMMENDATIONS
        return (is_rec, -URGENCY.get(r.conclusion, 0), -r.cf, -r.specificity)
    return sorted(candidates, key=key)


CONFLICT_STRATEGIES = {
    "highest_cf": resolve_highest_cf,
    "most_specific": resolve_most_specific,
    "safety_first": resolve_safety_first,
}


def forward_chain(observations: Dict[str, float], rule_base=None,
                   strategy: str = "safety_first", max_iterations: int = 20,
                   halt_on_goal: bool = True) -> TriageResult:
    rule_base = rule_base or RULE_BASE
    resolver = CONFLICT_STRATEGIES[strategy]
    facts = dict(observations)
    trace: List[FiredRule] = []
    fired_ids = set()
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        candidates = [r for r in rule_base if r.applicable(facts) and r.rule_id not in fired_ids]
        if not candidates:
            break
        rule = resolver(candidates)[0]
        prior = facts.get(rule.conclusion)
        new_cf = rule.cf if prior is None else combine_cf(prior, rule.cf)
        facts[rule.conclusion] = new_cf
        fired_ids.add(rule.rule_id)
        trace.append(FiredRule(rule.rule_id, list(rule.conditions), rule.conclusion,
                                rule.cf, rule.rationale, iteration))
        if halt_on_goal and rule.conclusion in RECOMMENDATIONS:
            break

    derived_recs = {k: v for k, v in facts.items() if k in RECOMMENDATIONS}
    if not derived_recs:
        recommendation, certainty = "HOME_CARE", 0.30
    elif strategy == "safety_first":
        recommendation = max(derived_recs, key=lambda r: (URGENCY[r], derived_recs[r]))
        certainty = derived_recs[recommendation]
    else:
        recommendation = max(derived_recs, key=lambda r: derived_recs[r])
        certainty = derived_recs[recommendation]

    return TriageResult(recommendation, certainty, trace, facts, iteration, strategy)

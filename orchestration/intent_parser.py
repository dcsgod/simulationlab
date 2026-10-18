"""
Rule-based and semantic intent parser translating natural language queries to simulation inputs.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
import re
from pydantic import BaseModel, Field

from mathematical_engine.contracts.inputs import InterventionType


class IntentType(str, Enum):
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    SENSITIVITY = "sensitivity"
    EXPLAIN = "explain"
    UNKNOWN = "unknown"


class ParsedIntervention(BaseModel):
    variable_name: str
    intervention_type: InterventionType
    value: float
    raw_text: Optional[str] = None


class ParsedIntent(BaseModel):
    intent_type: IntentType
    target_metric: Optional[str] = None
    interventions: List[ParsedIntervention] = Field(default_factory=list)
    optimization_goal: Optional[str] = None
    confidence: float = 1.0
    raw_prompt: str


class IntentParser:
    """
    Parses business questions into structured execution intents.
    """

    # Mapping keywords to canonical variable names
    _VAR_MAP = {
        "promotional discount": "promo_discount_pct",
        "promo discount": "promo_discount_pct",
        "promotion discount": "promo_discount_pct",
        "discount": "promo_discount_pct",
        "promo": "promo_discount_pct",
        "price": "base_price",
        "base price": "base_price",
        "effective price": "effective_price",
        "volume": "units_sold",
        "quantity": "units_sold",
        "units": "units_sold",
        "sales": "net_sales_usd",
        "revenue": "net_sales_usd",
        "gross margin": "gross_margin_usd",
        "margin": "gross_margin_usd",
        "gross profit": "gross_margin_usd",
        "profit": "gross_margin_usd",
        "cogs": "cogs_usd",
        "cost": "cogs_usd",
        "demand": "peak_demand_mw",
        "generation": "generation_mwh",
    }

    @classmethod
    def parse(cls, prompt: str) -> ParsedIntent:
        text = prompt.strip().lower()

        # 1. Detect Optimization
        if any(w in text for w in ["optimize", "optimization", "minimize", "maximize", "best allocation"]):
            goal = "maximize_profit" if "profit" in text or "margin" in text else "minimize_cost"
            return ParsedIntent(
                intent_type=IntentType.OPTIMIZATION,
                optimization_goal=goal,
                raw_prompt=prompt,
                confidence=0.9,
            )

        # 2. Detect Sensitivity
        if any(w in text for w in ["sensitivity", "elasticity", "key drivers", "what drives"]):
            target = cls._extract_target(text)
            return ParsedIntent(
                intent_type=IntentType.SENSITIVITY,
                target_metric=target or "gross_margin_usd",
                raw_prompt=prompt,
                confidence=0.88,
            )

        # 3. Detect Simulation & Interventions
        interventions: List[ParsedIntervention] = []

        # Regex for: "[variable] increases/decreases by X%" or "X% increase/cut in [variable]"
        # Pattern A: (variable) (increases|decreases|rises|falls|drops|cuts) by ([0-9.]+)%?
        pat_a = re.finditer(
            r"([a-z\s]+?)\s+(increases?|decreases?|rises?|falls?|drops?|cuts?|goes up|goes down)\s+by\s+([0-9.]+)\s*(%|percent)?",
            text
        )
        for m in pat_a:
            var_raw = m.group(1).strip()
            direction = m.group(2)
            num_val = float(m.group(3))
            is_pct = bool(m.group(4)) or "%" in m.group(0)

            # Map variable
            canonical_var = cls._match_variable(var_raw)
            if canonical_var:
                sign = -1.0 if any(d in direction for d in ["dec", "fall", "drop", "cut", "down"]) else 1.0
                val = sign * num_val
                int_type = InterventionType.PERCENTAGE_DELTA if is_pct else InterventionType.ABSOLUTE_DELTA
                interventions.append(
                    ParsedIntervention(
                        variable_name=canonical_var,
                        intervention_type=int_type,
                        value=val,
                        raw_text=m.group(0),
                    )
                )

        # Pattern B: ([0-9.]+)%? (increase|decrease|cut|drop|rise) in ([a-z\s]+)
        pat_b = re.finditer(
            r"([0-9.]+)\s*(%|percent)?\s+(increase|decrease|cut|drop|rise|reduction)\s+in\s+([a-z\s]+)",
            text
        )
        for m in pat_b:
            num_val = float(m.group(1))
            is_pct = bool(m.group(2)) or "%" in m.group(0)
            direction = m.group(3)
            var_raw = m.group(4).strip()

            canonical_var = cls._match_variable(var_raw)
            if canonical_var:
                sign = -1.0 if any(d in direction for d in ["dec", "fall", "drop", "cut", "down", "reduct"]) else 1.0
                val = sign * num_val
                int_type = InterventionType.PERCENTAGE_DELTA if is_pct else InterventionType.ABSOLUTE_DELTA
                interventions.append(
                    ParsedIntervention(
                        variable_name=canonical_var,
                        intervention_type=int_type,
                        value=val,
                        raw_text=m.group(0),
                    )
                )

        target = cls._extract_target(text)

        intent_type = IntentType.SIMULATION if interventions or target else IntentType.UNKNOWN

        return ParsedIntent(
            intent_type=intent_type,
            target_metric=target or "gross_margin_usd",
            interventions=interventions,
            raw_prompt=prompt,
            confidence=0.92 if interventions else 0.7,
        )

    @classmethod
    def _match_variable(cls, raw: str) -> Optional[str]:
        cleaned = raw.lower().strip()
        for k, v in cls._VAR_MAP.items():
            if k in cleaned:
                return v
        return None

    @classmethod
    def _extract_target(cls, text: str) -> Optional[str]:
        # Target usually follows "what happens to [target]" or "impact on [target]"
        m = re.search(r"(?:what happens to|impact on|effect on|affect)\s+([a-z\s]+?)(?:\s+if|\s+when|\?|$)", text)
        if m:
            matched_raw = m.group(1).strip()
            return cls._match_variable(matched_raw)
        
        # Fallback keyword match
        for k, v in [("gross margin", "gross_margin_usd"), ("profit", "gross_margin_usd"), ("revenue", "net_sales_usd"), ("sales", "net_sales_usd")]:
            if k in text:
                return v
        return None

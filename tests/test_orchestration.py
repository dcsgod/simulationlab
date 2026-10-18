"""
Tests for Orchestration (Intent Parsing, Scenario Planning, Routing, Grounded Evidence Envelope).
"""
import pytest
from connectors import MockDataProvider
from orchestration import (
    IntentType,
    IntentParser,
    ScenarioPlanner,
    ModelRouter,
    MLModelProvider,
)
from mathematical_engine.contracts.inputs import InterventionType


class TestIntentParser:
    def test_promo_discount_intent(self):
        prompt = "What happens to gross margin if promotional discount increases by 5%?"
        intent = IntentParser.parse(prompt)

        assert intent.intent_type == IntentType.SIMULATION
        assert intent.target_metric == "gross_margin_usd"
        assert len(intent.interventions) == 1
        interv = intent.interventions[0]
        assert interv.variable_name == "promo_discount_pct"
        assert interv.intervention_type == InterventionType.PERCENTAGE_DELTA
        assert interv.value == 5.0

    def test_price_cut_intent(self):
        prompt = "What happens to revenue if price cuts by 10%?"
        intent = IntentParser.parse(prompt)

        assert intent.intent_type == IntentType.SIMULATION
        assert intent.target_metric == "net_sales_usd"
        assert len(intent.interventions) == 1
        interv = intent.interventions[0]
        assert interv.variable_name == "base_price"
        assert interv.value == -10.0

    def test_optimization_intent(self):
        prompt = "Optimize generation dispatch to minimize cost"
        intent = IntentParser.parse(prompt)
        assert intent.intent_type == IntentType.OPTIMIZATION
        assert intent.optimization_goal == "minimize_cost"


class TestOrchestrationPipeline:
    def setup_method(self):
        self.provider = MockDataProvider()
        self.router = ModelRouter(data_provider=self.provider)

    def test_end_to_end_retail_query(self):
        query = "What happens to gross margin if promotional discount increases by 5%?"
        intent = IntentParser.parse(query)
        envelope = self.router.route_and_execute(intent)

        assert envelope.execution_status == "success"
        assert "gross_margin_usd" in envelope.metric_deltas
        assert len(envelope.interventions_applied) == 1
        assert envelope.validation_passed is True
        assert len(envelope.grounded_summary) > 0
        assert "gross_margin_usd" in envelope.grounded_summary
        assert "promo_discount_pct" in envelope.grounded_summary


class TestMLProvider:
    def test_deterministic_fallback(self):
        provider = MLModelProvider()
        pred = provider.predict_surrogate({"price": 20.0, "volume": 5.0})
        assert pred == 100.0

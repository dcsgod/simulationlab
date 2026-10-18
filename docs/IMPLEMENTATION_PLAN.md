# Simulation Lab: Implementation Plan

## 1. Executive Summary & Vision
Simulation Lab is a universal, ontology-driven, explainable simulation and optimization platform. It connects to enterprise data (such as Databricks / Unity Catalog or local mock sources), discovers business semantics, constructs a validated ontology and dependency DAG, runs deterministic, stochastic, and optimization models, explains results with grounded execution evidence, and exposes capabilities through an interactive web interface and natural language planner.

## 2. Current Repository State
- **Root Directory**: `d:\simulationlab`
- **Existing Files**:
  - `pyproject.toml` (basic placeholder)
  - `main.py` (placeholder)
  - `mathematical_engine/` (directory with 0-byte skeleton files created previously; needs complete implementation)
  - Python 3.11 virtual environment available with `uv` package manager. Node.js v24.16.0 and npm 11.13.0 installed.
- **Status**: Blank canvas with established target structure. No legacy runtime code exists yet.

---

## 3. Architecture Blueprint

```
+---------------------------------------------------------------------------------------+
|                                    Frontend (Vite / React / TS)                       |
|  [Dashboard] [Data Sources] [Ontology Explorer] [DAG Explorer] [Scenario Builder]    |
|                [Simulation Results] [Optimization Workspace] [Chat / Copilot]         |
+-------------------------------------------+-------------------------------------------+
                                            | REST API / SSE
+-------------------------------------------v-------------------------------------------+
|                               FastAPI Application Layer                               |
|  /api/health  /api/connectors  /api/discovery  /api/ontology  /api/dag  /api/models   |
|  /api/scenarios  /api/simulations  /api/optimization  /api/explainability  /api/chat  |
+-------------------+-----------------------+-------------------+-----------------------+
                    |                       |                   |
+-------------------v---+   +---------------v---+   +-----------v-----------+
| Orchestration         |   | Ontology & DAG    |   | Connectors            |
| - Intent Parser       |   | - Canonical Model |   | - Databricks (UC, SQL)|
| - Scenario Planner    |   | - Discovery       |   | - Mock Provider       |
| - Execution Planner   |   | - Dependency DAG  |   | - Metadata Profiler   |
+-------------------+---+   +---------------+---+   +-----------------------+
                    |                       |
+-------------------v-----------------------v-------------------------------------------+
|                          Mathematical Engine (Independent Core)                       |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  | Contracts & Core      | | Deterministic Engine  | | Stochastic & Uncertainty     | |
|  | - Scenario, Variable  | | - AST Formula Evaluator| | - Monte Carlo (Corr, Dist) | |
|  | - Model Registry, Base| | - DAG Propagation     | | - Risk Metrics (VaR, CVaR)   | |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  | Optimization Core     | | Sensitivity Analysis  | | Industry Packs               | |
|  | - LP, MILP (HiGHS)    | | - Local / Finite Diff | | - Retail (Margin, Promo)     | |
|  | - Slack & Infeasibility| | - Global (Sobol/Morris)| - Energy (Dispatch & Storage)  | |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  +----------------------------------------------------------------------------------+ |
|  | Explainability, Validation Invariants, Execution Traces & Grounded Evidence      | |
|  +----------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------+
```

---

## 4. Phased Delivery Roadmap & Acceptance Criteria

### Phase 1: Mathematical Engine Foundation
- [x] Fix/clean `mathematical_engine` directory structure (rename `init.py` to `__init__.py`, set up proper packages).
- [x] Define shared Pydantic v2 contracts (`Scenario`, `BaselineState`, `Intervention`, `NumericVariable`, `Unit`, `SimulationResult`, `ExecutionTrace`, etc.).
- [x] Implement AST-based safe formula evaluator (no `eval()`/`exec()`), cycle detection, DAG topological order, and propagation.
- [x] Implement BaseModel and ModelRegistry with capability matching and validation requirements.
- [x] Implement domain bounds, invariants, and diagnostic checking.
- [x] Write unit tests for analytical formula execution, cyclic errors, unit consistency, and DAG propagation.

### Phase 2: Stochastic Simulation, Sensitivity, and Optimization
- [x] Implement Monte Carlo engine supporting Normal, Lognormal, Uniform, Triangular, and Correlated inputs (Cholesky decomposition with PSD validation).
- [x] Implement Risk Metrics (Mean, Std, VaR, CVaR, Quantiles, breach probabilities).
- [x] Implement Sensitivity Analysis (OAT, finite difference, global parameter ranking).
- [x] Implement Optimization Core (Linear and Mixed-Integer Linear Programming using SciPy HiGHS solver abstraction, decision variables, bounds, equality/inequality constraints, slack analysis, infeasibility diagnostics).
- [x] Add rigorous property-based and analytical correctness tests.

### Phase 3: Data Connectors & Governance
- [x] Implement `BaseDataProvider` abstraction.
- [x] Implement `MockDataProvider` with realistic synthetic enterprise datasets (Retail, Energy).
- [x] Implement `DatabricksConnector` with configuration validation, token masking, schema/table discovery, safe parameterized query executor, and bounded sampling.
- [x] Implement metadata caching and freshness tracking.
- [x] Unit & integration tests for mock and Databricks connectors (with graceful skip when offline).

### Phase 4: Ontology & Dependency DAG Services
- [x] Implement canonical entity models (Entity, Attribute, Relationship, UnitRegistry).
- [x] Implement automated discovery rules mapping schema columns to ontology concepts.
- [x] Implement DAG builder with edge typing (Semantic, Calculation, Data, Causal Hypothesis, Validated Causal Effect, Constraint).
- [x] Topological validation, cycle rejection, ancestor/descendant impact analysis.
- [x] In-memory and versioned graph persistence repository.

### Phase 5: Model Routing, Orchestration, and Explainability
- [x] Implement capability-based model router.
- [x] Implement Intent Parser and Scenario Planner for natural language queries.
- [x] Implement Grounded Evidence Envelope generation (baselines, interventions, formula trace, sensitivity drivers, validation status).
- [x] Implement optional Hugging Face / MLflow provider abstraction with deterministic fallback.

### Phase 6: FastAPI Backend
- [x] Implement clean REST endpoints covering `/api/health`, `/api/connectors`, `/api/discovery`, `/api/ontology`, `/api/dag`, `/api/models`, `/api/scenarios`, `/api/simulations`, `/api/optimization`, `/api/explainability`, `/api/chat`.
- [x] Structured error handlers, request ID middleware, validation envelopes.
- [x] Complete API integration test suite using FastAPI `TestClient`.

### Phase 7: Industry Packs
- [x] Retail Pack: Price elasticity, promotional markdown, demand-response, gross margin, inventory constraints.
- [x] Energy Pack: Generation mix, renewable intermittency, battery storage dispatch, peak demand, operating costs, emissions.

### Phase 8: Full-Stack Frontend Workspace
- [x] Modern React + TypeScript + Vite frontend.
- [x] Dashboard, Data Source Explorer, Ontology & DAG Explorer (interactive visual graphs), Scenario Builder, Simulation Results (KPI deltas, charts, distributions), Optimization Workspace, and Natural-Language Assistant.
- [x] Technical UI aesthetics (clean white/charcoal/neutral surfaces, royal-blue accents, high information density).

---

## 5. Verification & Acceptance Criteria
1. Mathematical engine passes 100% of unit & analytical tests without external services.
2. Monte Carlo runs reproducibly with fixed seeds.
3. SciPy HiGHS solves MILP/LP problems and reports slack/infeasibility accurately.
4. Databricks connector operates securely with live credentials or gracefully falls back to mock provider in demo mode.
5. End-to-end retail scenario ("What happens to gross margin if promotional discount increases by 5%?") runs from NL to mathematical simulation, graph traversal, and explainability evidence.

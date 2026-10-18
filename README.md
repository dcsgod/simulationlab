# Veridex

> **Universal, Ontology-Driven, Explainable Enterprise Simulation & Optimization Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6.svg)](https://www.typescriptlang.org)
[![SciPy HiGHS](https://img.shields.io/badge/Solver-SciPy_HiGHS-orange.svg)](https://scipy.org)
[![Databricks](https://img.shields.io/badge/Lakehouse-Databricks_UC-FF3621.svg)](https://www.databricks.com)
[![Tests Passing](https://img.shields.io/badge/tests-49%20passed%20(100%25)-success.svg)](file:///d:/simulationlab/tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Executive Summary

**Veridex** is an enterprise-grade decision intelligence platform designed to replace black-box approximations and opaque spreadsheets with **formal, grounded, verifiable mathematical simulation and optimization**.

It connects natively to enterprise data sources (including live **Databricks Unity Catalog** and local lakehouse providers), discovers business semantics, constructs a topological dependency DAG, executes deterministic and stochastic models, solves mixed-integer optimization problems using **SciPy HiGHS**, and delivers **Grounded Evidence Envelopes** that explain every number through auditable execution traces.

---

## 2. Architecture Blueprint

```
+---------------------------------------------------------------------------------------+
|                                    Frontend (Vite / React / TS)                       |
|  [Dashboard] [Data Sources] [Ontology Explorer] [DAG Explorer] [Scenario Builder]    |
|                [Simulation Results] [Optimization Workspace] [Copilot Chat]           |
+-------------------------------------------+-------------------------------------------+
                                            | REST API / SSE (Proxy :5173 -> :8000)
+-------------------------------------------v-------------------------------------------+
|                               FastAPI Application Layer                               |
|  /api/health  /api/connectors  /api/discovery  /api/ontology  /api/dag  /api/models   |
|  /api/scenarios  /api/simulations  /api/optimization  /api/explainability  /api/chat  |
+-------------------+-----------------------+-------------------+-----------------------+
                    |                       |                   |
+-------------------v---+   +---------------v---+   +-----------v-----------+
| Orchestration         |   | Ontology & DAG    |   | Connectors            |
| - Intent Parser       |   | - Canonical Model |   | - Databricks (UC, SQL)|
| - Scenario Planner    |   | - Auto Discovery  |   | - Mock Lakehouse      |
| - Evidence Envelope   |   | - Dependency DAG  |   | - Metadata Profiler   |
+-------------------+---+   +---------------+---+   +-----------------------+
                    |                       |
+-------------------v-----------------------v-------------------------------------------+
|                          Mathematical Engine (Independent Core)                       |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  | Contracts & Core      | | Deterministic Engine  | | Stochastic & Uncertainty     | |
|  | - Scenario, Variable  | | - AST Formula Evaluator| | - Monte Carlo (Corr, Copula)| |
|  | - Model Registry, Base| | - DAG Propagation     | | - Risk Metrics (VaR, CVaR)   | |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  | Optimization Core     | | Sensitivity Analysis  | | Industry Packs               | |
|  | - LP, MILP (HiGHS)    | | - Local / Finite Diff | | - Retail (Margin, Promo)     | |
|  | - Slack & Duality     | | - Global (Morris)     | | - Energy (Dispatch & Battery)| |
|  +-----------------------+ +-----------------------+ +------------------------------+ |
|  +----------------------------------------------------------------------------------+ |
|  | Explainability, Validation Invariants, Execution Traces & Grounded Evidence      | |
|  +----------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------+
```

---

## 3. Core Architectural Pillars

### 1. Zero-Hallucination Safe AST Evaluation
- Uses a strict whitelist-only Python Abstract Syntax Tree (AST) visitor.
- Evaluates algebraic formulas without ever using `eval()`, `exec()`, or allowing dynamic imports or arbitrary method calls.
- Automatically extracts referenced identifiers to construct computational graphs.

### 2. Topological DAG & Cycle Rejection
- Directed computational graphs are ordered using Kahn's algorithm.
- Cycle detection (Tarjan/DFS) detects cyclic dependencies and provides actionable error paths before evaluation begins.
- Ancestor driver tracing and descendant impact analysis allow full what-if impact discovery.

### 3. Stochastic Uncertainty & Copula Sampling
- Univariate distributions: Normal, Lognormal, Uniform, Triangular, Constant.
- Multivariate Gaussian Copula with Cholesky decomposition and Higham positive semi-definite projection for correlated inputs.
- Empirical statistical moments, empirical percentiles (p5, p25, median, p75, p95), Value at Risk ($VaR_{95}$), and Conditional Value at Risk ($CVaR_{95}$ / Expected Shortfall).

### 4. SciPy HiGHS LP & MILP Solver
- Direct wrapper around SciPy's embedded C++ HiGHS solver.
- Solves continuous Linear Programs (LP) and Mixed-Integer Linear Programs (MILP) with 0-1 binary variables.
- Calculates exact constraint slacks to distinguish binding bottleneck constraints from surplus capacity.
- Diagnoses contradictory or infeasible constraint boundaries.

### 5. Databricks Unity Catalog & Synthetic Lakehouse
- Native connection to Databricks SQL Warehouses and Unity Catalog using `databricks-sql-connector`.
- Automatic Personal Access Token (PAT) masking ensuring credentials never appear in logs or client-facing responses.
- In-memory synthetic enterprise data provider with realistic Retail and Energy industry datasets.
- Schema caching with TTL and freshness tracking.

### 6. Grounded Evidence Envelopes & Copilot
- Translates natural language questions into structured interventions using rule-based and regex intent parsing.
- Generates immutable evidence envelopes recording baseline snapshots, parameter interventions, calculation formulas, sensitivity rankings, and invariant validation statuses.

---

## 4. Industry Simulation Packs

### Retail Pack
- **Price Elasticity & Promotional Markdown**: Constant elasticity demand response:
  $$Q_{new} = Q_0 \times \left(\frac{P_{eff}}{P_0}\right)^{\epsilon}$$
- **Margin & Revenue Impact**: Effective discount, unit cost scaling, and gross profit reconciliation.
- **Inventory Runway**: Days of supply, carrying cost calculation, and stockout probability scoring.

### Energy & Utilities Pack
- **Merit-Order Economic Dispatch**: Lowest marginal cost dispatch (Solar & Wind at $0/MWh $\rightarrow$ Natural Gas CCGT $\rightarrow$ Peaker Gas) to satisfy hourly net load.
- **Carbon Accounting**: Dynamic $CO_2$ tonnage tracking per MWh generated.
- **Battery Energy Storage (BESS) Arbitrage**: State-of-Charge (SoC) management, roundtrip efficiency losses, and peak-shaving price arbitrage.

---

## 5. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm 9+
- `uv` (recommended) or `pip`

### 1. Clone & Setup Python Virtual Environment

```bash
git clone https://github.com/dcsgod/simulationlab.git veridex
cd veridex

# Create and activate virtual environment
uv venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# Install core dependencies
uv pip install -e ".[dev,advanced-math,databricks]"
```

### 2. Launch the FastAPI Backend

```bash
python main.py
# Server runs on http://127.0.0.1:8000
# Interactive API documentation: http://127.0.0.1:8000/docs
```

### 3. Launch the Frontend Workspace

```bash
cd frontend
npm install
npm run dev
# Interactive UI runs on http://127.0.0.1:5173
```

---

## 6. Running Tests

The test suite runs with 100% isolation without requiring external network services:

```bash
python -m pytest -v
```

```
============================= test session starts =============================
collected 49 items

tests/test_api_integration.py ................ PASSED
tests/test_connectors.py ..................... PASSED
tests/test_industry_packs.py ................. PASSED
tests/test_ontology_service.py ............... PASSED
tests/test_orchestration.py .................. PASSED
mathematical_engine/tests/test_phase1_core.py  PASSED
mathematical_engine/tests/test_phase2_advanced.py PASSED

======================== 49 passed in 3.83s =========================
```

---

## 7. Connecting to Databricks Unity Catalog

To connect to your Databricks workspace:

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate `DATABRICKS_TOKEN`, `DATABRICKS_SERVER_HOSTNAME`, and `DATABRICKS_HTTP_PATH`.
3. In the UI, navigate to **Data Sources** $\rightarrow$ **Databricks Unity Catalog (Live)** to test the live connection.
4. Or configure dynamically via the REST API:

```bash
curl -X POST "http://127.0.0.1:8000/api/connectors/databricks/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "server_hostname": "your-workspace.cloud.databricks.com",
    "http_path": "/sql/1.0/warehouses/your-warehouse-id",
    "access_token": "dapi...",
    "catalog": "workspace",
    "schema_name": "default"
  }'
```

---

## 8. License

Distributed under the MIT License. See `LICENSE` for details.

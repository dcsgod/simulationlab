# Simulation Lab: Architectural Decisions (ADR)

## ADR-001: Separation of Mathematical Engine from Frameworks
- **Decision**: Keep the `mathematical_engine` completely independent of FastAPI, Databricks SDKs, database drivers, LangGraph, and UI code.
- **Rationale**: The mathematical core must be 100% deterministic, testable in pure isolation, and embeddable anywhere without heavy dependency baggage.
- **Consequences**: Pure numerical models take typed contracts and return structured outputs. Serialization and persistence are handled in higher layers.

## ADR-002: Safe AST Expression Evaluation over `eval()`
- **Decision**: All formula evaluations are executed using a whitelist-only Python Abstract Syntax Tree (AST) visitor.
- **Rationale**: User or generated formulas must never have access to `__import__`, builtins, execution environments, filesystem, or arbitrary method calls.
- **Allowed Operations**: Basic arithmetic (`+`, `-`, `*`, `/`, `**`, `//`, `%`, unary minus), standard safe math functions (`log`, `exp`, `sqrt`, `min`, `max`, `abs`, `clip`, `round`), and bounded variable identifiers.

## ADR-003: Direct SciPy HiGHS Solver Abstraction for LP and MILP
- **Decision**: Use `scipy.optimize.linprog(method='highs')` and `scipy.optimize.milp` as the primary optimization backend, wrapped with a clean problem formulation interface.
- **Rationale**: SciPy is already a standard dependency, and its embedded HiGHS solver is state-of-the-art for LP and MILP. It requires no external binaries or difficult licensing, running reliably across Windows, Linux, and macOS.
- **Consequences**: Standard LP and MILP problems run out-of-the-box with exact duality/slack reporting and infeasibility detection.

## ADR-004: Dual-Mode Data Connectivity (Mock & Databricks)
- **Decision**: Implement a unified `BaseDataProvider` with both `MockDataProvider` and `DatabricksConnector`.
- **Rationale**: Enables zero-setup local development, testing, and offline demonstrations while supporting production Unity Catalog / Databricks SQL when configured with credentials.
- **Consequences**: The system operates with full functionality out of the box in synthetic demo mode, clearly labeling synthetic vs. live data.

## ADR-005: Grounded Explainability & Evidence Envelope
- **Decision**: Every simulation or optimization run produces an immutable Evidence Envelope linking baseline snapshot, exact parameter interventions, mathematical formula/model version, DAG traversal path, sensitivity ranking, and invariant validation results.
- **Rationale**: Enterprise decision-makers must never be presented with hallucinated numbers or opaque black-box recommendations. All numbers are verifiable against the underlying equations and data snapshots.

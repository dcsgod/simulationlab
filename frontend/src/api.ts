/**
 * Simulation Lab REST API client.
 */

export interface HealthStatus {
  status: string;
  service: string;
  timestamp: number;
  python_version: string;
}

export interface DataSourceMetadata {
  source_id: string;
  name: string;
  source_type: string;
  is_connected: boolean;
  catalogs: string[];
  last_synced_at?: number;
}

export interface ColumnDefinition {
  name: string;
  data_type: string;
  is_nullable: boolean;
  is_numeric: boolean;
  min_value?: number;
  max_value?: number;
  mean_value?: number;
  distinct_count?: number;
  sample_values?: any[];
}

export interface TableSchema {
  catalog_name: string;
  schema_name: string;
  table_name: string;
  columns: ColumnDefinition[];
  row_count_estimate?: number;
}

export interface EntityNode {
  id: string;
  name: string;
  entity_type: string;
  description?: string;
  data_type: string;
  unit?: string;
  formula?: string;
  min_bound?: number;
  max_bound?: number;
  source_table?: string;
}

export interface RelationshipEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
  weight?: number;
  formula_expression?: string;
  confidence: number;
}

export interface OntologyGraph {
  graph_id: string;
  name: string;
  version: number;
  nodes: Record<string, EntityNode>;
  edges: RelationshipEdge[];
}

export interface MetricDelta {
  variable_name: string;
  baseline_value: number;
  scenario_value: number;
  absolute_delta: number;
  percentage_delta?: number;
  unit?: string;
}

export interface DistributionSummary {
  variable_name: string;
  mean: number;
  std: number;
  median: number;
  min_val: number;
  max_val: number;
  p5: number;
  p25: number;
  p75: number;
  p95: number;
  var_95?: number;
  cvar_95?: number;
  samples_count: number;
}

export interface SensitivityDriver {
  variable_name: string;
  target_metric: string;
  elasticity: number;
  absolute_derivative: number;
  normalized_impact: number;
  rank: number;
  direction: string;
}

export interface SimulationResult {
  simulation_id: string;
  scenario_id: string;
  status: string;
  metrics: Record<string, MetricDelta>;
  all_values: Record<string, number>;
  distributions: Record<string, DistributionSummary>;
  sensitivity_drivers: SensitivityDriver[];
  traces: any[];
  validation_passed: boolean;
  invariants_checked: number;
  invariants_violated: string[];
  execution_time_ms: number;
}

export interface Scenario {
  id: string;
  name: string;
  description?: string;
  baseline?: any;
  interventions: any[];
  target_variables: string[];
  assumptions?: Record<string, any>;
  tags?: string[];
}

export interface OptimizationResult {
  problem_name: string;
  status: string;
  is_optimal: boolean;
  objective_value?: number;
  variable_values: Record<string, number>;
  constraint_slacks: Record<string, number>;
  diagnostics: string[];
  solve_time_ms: number;
}

export interface EvidenceEnvelope {
  envelope_id: string;
  scenario_id: string;
  scenario_title: string;
  execution_status: string;
  baseline_snapshot_id: string;
  data_source_id: string;
  baseline_values: Record<string, number>;
  interventions_applied: any[];
  calculation_path: string[];
  execution_traces: any[];
  metric_deltas: Record<string, MetricDelta>;
  distributions: Record<string, DistributionSummary>;
  sensitivity_drivers: SensitivityDriver[];
  validation_passed: boolean;
  invariants_checked: number;
  invariants_violated: string[];
  grounded_summary: string;
}

export interface ChatResponse {
  user_query: string;
  intent: any;
  envelope: EvidenceEnvelope;
  reply: string;
}

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchConnectors(): Promise<DataSourceMetadata[]> {
  const res = await fetch(`${API_BASE}/connectors`);
  return res.json();
}

export async function fetchTables(sourceId: string, catalog: string, schema: string): Promise<TableSchema[]> {
  const res = await fetch(`${API_BASE}/connectors/${sourceId}/tables?catalog=${catalog}&schema=${schema}`);
  const data = await res.json();
  return data.tables || [];
}

export async function sampleTable(sourceId: string, catalog: string, schema: string, table: string, limit: number = 20) {
  const res = await fetch(`${API_BASE}/connectors/${sourceId}/sample?catalog=${catalog}&schema=${schema}&table=${table}&limit=${limit}`);
  return res.json();
}

export async function runDiscovery(sourceId: string, catalog: string, schemaName: string) {
  const res = await fetch(`${API_BASE}/discovery/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_id: sourceId, catalog, schema_name: schemaName }),
  });
  return res.json();
}

export async function fetchOntology(): Promise<OntologyGraph> {
  const res = await fetch(`${API_BASE}/ontology`);
  return res.json();
}

export async function fetchDAG() {
  const res = await fetch(`${API_BASE}/dag`);
  return res.json();
}

export async function fetchDAGImpact(nodeName: string) {
  const res = await fetch(`${API_BASE}/dag/impact/${nodeName}`);
  return res.json();
}

export async function fetchScenarioTemplates(): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/scenarios/templates`);
  return res.json();
}

export async function runSimulation(payload: {
  scenario_id?: string;
  scenario?: any;
  mode?: string;
  num_iterations?: number;
  seed?: number;
}): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/simulations/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function solveOptimization(payload: { template_name?: string; problem?: any }): Promise<OptimizationResult> {
  const res = await fetch(`${API_BASE}/optimization/solve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  return res.json();
}

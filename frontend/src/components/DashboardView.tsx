import React from 'react';
import { 
  Activity, 
  Cpu, 
  Database, 
  Network, 
  ShieldCheck, 
  TrendingUp, 
  CheckCircle2, 
  ArrowRight,
  Sparkles,
  Zap
} from 'lucide-react';
import { OntologyGraph, DataSourceMetadata } from '../api';

interface DashboardViewProps {
  ontology: OntologyGraph | null;
  connectors: DataSourceMetadata[];
  setActiveTab: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ ontology, connectors, setActiveTab }) => {
  const nodeCount = ontology ? Object.keys(ontology.nodes).length : 12;
  const edgeCount = ontology ? ontology.edges.length : 14;

  const cards = [
    { label: 'Canonical Concepts', value: nodeCount, icon: Network, color: '#3b82f6', change: '+3 derived' },
    { label: 'Calculation Edges', value: edgeCount, icon: Zap, color: '#8b5cf6', change: '100% acyclic' },
    { label: 'Active Solvers', value: 'HiGHS (C++)', icon: Cpu, color: '#10b981', change: 'LP & MILP' },
    { label: 'Data Sources', value: `${connectors.length} Connected`, icon: Database, color: '#f59e0b', change: 'Retail & Energy' },
  ];

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Hero Banner */}
      <div style={{
        padding: '2rem',
        borderRadius: 'var(--radius-lg)',
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
        border: '1px solid var(--border-subtle)',
        marginBottom: '2rem',
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.25rem 0.65rem', borderRadius: 'var(--radius-full)', background: 'rgba(37, 99, 235, 0.15)', color: '#60a5fa', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Sparkles size={14} /> Production Ready Mathematical Engine
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '0.5rem' }}>
            Simulation Lab Workspace
          </h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '700px', fontSize: '0.95rem' }}>
            Universal, ontology-driven simulation and optimization platform. Discover business semantics from Unity Catalog lakehouses, run deterministic or Monte Carlo risk simulations, and inspect verified mathematical execution traces.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setActiveTab('simulations')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-blue)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.875rem',
              boxShadow: '0 4px 12px var(--accent-blue-glow)',
            }}
          >
            Launch Simulation <ArrowRight size={16} />
          </button>
          <button
            onClick={() => setActiveTab('copilot')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)',
              fontWeight: 600,
              fontSize: '0.875rem',
            }}
          >
            Ask Copilot
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i} style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{c.label}</span>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: `${c.color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Icon size={18} color={c.color} />
                </div>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>{c.value}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{c.change}</div>
            </div>
          );
        })}
      </div>

      {/* Feature Grids */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Architectural Guarantees */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.5rem',
        }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={20} color="var(--accent-emerald)" /> Zero-Hallucination Guarantees
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {[
              { title: 'AST Safe Formula Evaluator', desc: 'Whitelist-only algebraic parser without eval() or arbitrary code execution.' },
              { title: 'Kahn Topological Ordering', desc: 'Strict DAG traversal preventing cyclic deadlock and out-of-order evaluation.' },
              { title: 'SciPy HiGHS Solver Abstraction', desc: 'Embedded C++ solver for deterministic LP & MILP with exact slack and dual analysis.' },
              { title: 'Grounded Evidence Envelope', desc: 'Immutable audit traces connecting scenario deltas directly to data snapshots.' },
            ].map((item, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                <CheckCircle2 size={16} color="var(--accent-emerald)" style={{ marginTop: '0.2rem', flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{item.title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Scenario Launchpad */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.5rem',
        }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={20} color="var(--accent-blue)" /> Scenario Launchpad
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              {
                title: 'Retail: 15% Promotional Price Markdown',
                desc: 'Simulate volume lift, gross sales, and net profit margin.',
                tab: 'simulations',
              },
              {
                title: 'Retail: $50,000 Marketing Allocation',
                desc: 'Solve Mixed-Integer Linear Program to maximize margin contribution.',
                tab: 'optimization',
              },
              {
                title: 'Energy: Grid Merit-Order Economic Dispatch',
                desc: 'Optimize solar, wind, CCGT, and peaker generation to meet 600 MW demand.',
                tab: 'optimization',
              },
            ].map((scen, idx) => (
              <div
                key={idx}
                onClick={() => setActiveTab(scen.tab)}
                style={{
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.15s ease',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{scen.title}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{scen.desc}</div>
                </div>
                <ArrowRight size={16} color="var(--text-muted)" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

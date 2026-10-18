import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  TrendingUp, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  Zap, 
  PieChart, 
  BarChart3,
  Sliders
} from 'lucide-react';
import { OptimizationResult, solveOptimization } from '../api';

export const OptimizationWorkspaceView: React.FC = () => {
  const [template, setTemplate] = useState<'retail_promo_allocation' | 'energy_dispatch_least_cost'>('retail_promo_allocation');
  const [budgetLimit, setBudgetLimit] = useState<number>(50000);
  const [targetLoad, setTargetLoad] = useState<number>(600);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);

  useEffect(() => {
    handleSolve();
  }, [template]);

  const handleSolve = async () => {
    setLoading(true);
    try {
      const res = await solveOptimization({ template_name: template });
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Cpu size={24} color="var(--accent-blue)" /> SciPy HiGHS Optimization Workspace
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Solve Linear (LP) and Mixed-Integer Linear Programs (MILP) with exact slack analysis and feasibility guarantees.
          </p>
        </div>

        {/* Template Switcher */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-card)',
          padding: '0.25rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
        }}>
          <button
            onClick={() => setTemplate('retail_promo_allocation')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              fontWeight: 600,
              background: template === 'retail_promo_allocation' ? 'var(--accent-blue)' : 'transparent',
              color: template === 'retail_promo_allocation' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            Retail Promo Allocation
          </button>
          <button
            onClick={() => setTemplate('energy_dispatch_least_cost')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              fontWeight: 600,
              background: template === 'energy_dispatch_least_cost' ? 'var(--accent-blue)' : 'transparent',
              color: template === 'energy_dispatch_least_cost' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            Energy Grid Dispatch (600 MW)
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.5rem' }}>
        {/* Left Problem Formulation */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={18} color="var(--accent-blue)" /> Problem Formulation
          </h2>

          {template === 'retail_promo_allocation' ? (
            <>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                <strong>Objective:</strong> Maximize Total Gross Margin Lift<br/>
                <code className="badge badge-blue font-mono" style={{ marginTop: '0.35rem', display: 'inline-block' }}>
                  Max 3.20*Bev + 2.80*Snk + 4.10*Org
                </code>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Subject to Constraints:
                </div>
                <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: 'var(--text-secondary)' }}>
                  <div>&bull; Total Budget &le; $50,000</div>
                  <div>&bull; Beverage Allocation &ge; $10,000</div>
                  <div>&bull; Snack Allocation &le; $20,000</div>
                  <div>&bull; Organic Allocation &le; $20,000</div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                <strong>Objective:</strong> Minimize Total Generation Operating Cost<br/>
                <code className="badge badge-blue font-mono" style={{ marginTop: '0.35rem', display: 'inline-block' }}>
                  Min 5*Sol + 8*Wnd + 48*CCGT + 95*Pk
                </code>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Subject to Constraints:
                </div>
                <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: 'var(--text-secondary)' }}>
                  <div>&bull; Grid Load Balance: Total Gen == 600 MW</div>
                  <div>&bull; Solar Capacity &le; 120 MW</div>
                  <div>&bull; Wind Capacity &le; 180 MW</div>
                  <div>&bull; CCGT Capacity &le; 400 MW</div>
                  <div>&bull; Peaker Capacity &le; 150 MW</div>
                </div>
              </div>
            </>
          )}

          <button
            onClick={handleSolve}
            disabled={loading}
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-blue)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.875rem',
              marginTop: '0.5rem',
              boxShadow: '0 4px 12px var(--accent-blue-glow)',
            }}
          >
            {loading ? 'Solving with HiGHS...' : 'Solve LP / MILP with HiGHS'}
          </button>
        </div>

        {/* Right Solution Analytics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {result && (
            <>
              {/* Summary Status Banner */}
              <div style={{
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                padding: '1.5rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span className="badge badge-emerald" style={{ fontSize: '0.8rem' }}>
                      <CheckCircle2 size={14} /> {result.status}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Solved in {result.solve_time_ms.toFixed(1)} ms
                    </span>
                  </div>
                  <h3 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                    {result.problem_name}
                  </h3>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Optimal Objective Value
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 900, color: '#34d399', fontFamily: 'var(--font-mono)' }}>
                    ${result.objective_value ? result.objective_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
                  </div>
                </div>
              </div>

              {/* Decision Variable Allocations */}
              <div style={{
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                padding: '1.5rem',
              }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <BarChart3 size={18} color="var(--accent-blue)" /> Optimal Decision Variables Assignment
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  {Object.entries(result.variable_values).map(([varName, val]) => (
                    <div
                      key={varName}
                      style={{
                        padding: '1rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {varName}
                      </div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0.25rem 0', fontFamily: 'var(--font-mono)' }}>
                        {template === 'retail_promo_allocation' ? `$${val.toLocaleString()}` : `${val.toFixed(1)} MW`}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#60a5fa' }}>Optimal Decision Variable</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Constraint Slack Analysis */}
              <div style={{
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                padding: '1.5rem',
              }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Zap size={18} color="var(--accent-amber)" /> Constraint Slacks &amp; Sensitivity Duality
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {Object.entries(result.constraint_slacks).map(([cName, slack]) => {
                    const isBinding = Math.abs(slack) < 1e-4;
                    return (
                      <div
                        key={cName}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem 1rem',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-surface)',
                          border: isBinding ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--border-subtle)',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{cName}</div>
                          <div style={{ fontSize: '0.75rem', color: isBinding ? '#fbbf24' : 'var(--text-muted)' }}>
                            {isBinding ? 'Binding (Bottleneck Constraint - Zero Slack)' : 'Non-binding (Surplus Slack)'}
                          </div>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <span className={isBinding ? 'badge badge-amber' : 'badge badge-blue'}>
                            Slack: {slack.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

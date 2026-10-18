import React, { useState, useEffect } from 'react';
import { 
  PlayCircle, 
  Dices, 
  TrendingUp, 
  TrendingDown, 
  Sliders, 
  ShieldCheck, 
  Activity, 
  HelpCircle,
  BarChart2,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';
import { 
  Scenario, 
  SimulationResult, 
  fetchScenarioTemplates, 
  runSimulation 
} from '../api';

export const SimulationStudioView: React.FC = () => {
  const [templates, setTemplates] = useState<Scenario[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('template_retail_promo_lift');
  const [mode, setMode] = useState<'deterministic' | 'monte_carlo'>('deterministic');
  const [numIterations, setNumIterations] = useState<number>(1000);
  const [promoDiscount, setPromoDiscount] = useState<number>(15.0);
  const [cogsInflation, setCogsInflation] = useState<number>(0.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResult | null>(null);

  useEffect(() => {
    fetchScenarioTemplates().then((tmpls) => {
      setTemplates(tmpls);
    }).catch(console.error);

    // Run initial demo simulation
    handleRun('deterministic', 15.0, 0.0);
  }, []);

  const handleRun = async (
    runMode: 'deterministic' | 'monte_carlo' = mode,
    promo: number = promoDiscount,
    cogs: number = cogsInflation
  ) => {
    setLoading(true);
    try {
      const interventions = [
        {
          target_variable: 'promo_discount_pct',
          intervention_type: 'set_value',
          value: promo,
          description: `${promo}% promotional markdown`,
        },
      ];
      if (Math.abs(cogs) > 0.01) {
        interventions.push({
          target_variable: 'cogs_usd',
          intervention_type: 'percentage_delta',
          value: cogs,
          description: `${cogs}% COGS adjustment`,
        });
      }

      const res = await runSimulation({
        scenario: {
          id: 'custom_studio_run',
          name: `Promotional Simulation (${promo}% Discount, ${cogs}% COGS)`,
          baseline: null,
          interventions,
          target_variables: ['promo_discount_pct', 'effective_price', 'units_sold', 'net_sales_usd', 'gross_margin_usd'],
        },
        mode: runMode,
        num_iterations: numIterations,
        seed: 42,
      });
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <PlayCircle size={24} color="var(--accent-blue)" /> Simulation &amp; What-If Studio
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Simulate business interventions, demand elasticity responses, and full Monte Carlo risk profiles.
          </p>
        </div>

        {/* Mode Toggle */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-card)',
          padding: '0.25rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
        }}>
          <button
            onClick={() => { setMode('deterministic'); handleRun('deterministic'); }}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              fontWeight: 600,
              background: mode === 'deterministic' ? 'var(--accent-blue)' : 'transparent',
              color: mode === 'deterministic' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            Deterministic DAG
          </button>
          <button
            onClick={() => { setMode('monte_carlo'); handleRun('monte_carlo'); }}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: mode === 'monte_carlo' ? 'var(--accent-blue)' : 'transparent',
              color: mode === 'monte_carlo' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            <Dices size={15} /> Monte Carlo (1,000 Draws)
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.5rem' }}>
        {/* Left Parameter Controls */}
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
            <Sliders size={18} color="var(--accent-blue)" /> Parameter Interventions
          </h2>

          {/* Promo Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600 }}>Promotional Discount</span>
              <span className="badge badge-blue font-mono">{promoDiscount}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="1"
              value={promoDiscount}
              onChange={(e) => setPromoDiscount(parseFloat(e.target.value))}
              style={{ width: '100%', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>0% (No promo)</span>
              <span>25%</span>
              <span>50% (Max)</span>
            </div>
          </div>

          {/* COGS Inflation Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600 }}>COGS Cost Adjustment</span>
              <span className="badge badge-amber font-mono">{cogsInflation > 0 ? `+${cogsInflation}%` : `${cogsInflation}%`}</span>
            </div>
            <input
              type="range"
              min="-20"
              max="30"
              step="1"
              value={cogsInflation}
              onChange={(e) => setCogsInflation(parseFloat(e.target.value))}
              style={{ width: '100%', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>-20% (Cost cut)</span>
              <span>0% (Baseline)</span>
              <span>+30% (Severe inflation)</span>
            </div>
          </div>

          {mode === 'monte_carlo' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: '0.4rem' }}>
                <span style={{ fontWeight: 600 }}>Monte Carlo Iterations</span>
                <span className="badge badge-purple font-mono">{numIterations}</span>
              </div>
              <select
                value={numIterations}
                onChange={(e) => setNumIterations(parseInt(e.target.value))}
                style={{ width: '100%', fontSize: '0.85rem' }}
              >
                <option value={500}>500 Samples (Fast)</option>
                <option value={1000}>1,000 Samples (Standard)</option>
                <option value={3000}>3,000 Samples (High Precision)</option>
              </select>
            </div>
          )}

          <button
            onClick={() => handleRun()}
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
            {loading ? 'Evaluating Model...' : 'Execute Simulation Run'}
          </button>

          {/* Domain Assumptions Notice */}
          <div style={{
            padding: '0.85rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
          }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>Active Microeconomic Laws:</div>
            <div style={{ color: 'var(--text-secondary)' }}>
              &bull; Constant Price Elasticity: &epsilon; = -1.45<br/>
              &bull; Demand equation: Q = Q0 &times; (P_eff / P0)^(-1.45)<br/>
              &bull; Gross Margin = Net Sales - COGS
            </div>
          </div>
        </div>

        {/* Right Output Dashboard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {result && (
            <>
              {/* Outcome KPI Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                {Object.entries(result.metrics).map(([name, m]) => {
                  const isPositive = m.absolute_delta >= 0;
                  const isMargin = name.includes('margin') || name.includes('profit');
                  const deltaColor = isPositive ? 'var(--accent-emerald)' : 'var(--accent-rose)';

                  return (
                    <div
                      key={name}
                      style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: '1.25rem',
                      }}
                    >
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                        {name.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, margin: '0.35rem 0', fontFamily: 'var(--font-mono)' }}>
                        {m.unit === 'USD' ? `$${m.scenario_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : m.scenario_value.toFixed(1)}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.775rem' }}>
                        <span style={{ color: deltaColor, fontWeight: 700, display: 'flex', alignItems: 'center' }}>
                          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                          {m.absolute_delta > 0 ? `+${m.absolute_delta.toFixed(1)}` : m.absolute_delta.toFixed(1)}
                          {m.percentage_delta !== null && m.percentage_delta !== undefined ? ` (${m.percentage_delta > 0 ? '+' : ''}${m.percentage_delta.toFixed(1)}%)` : ''}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>vs baseline</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Monte Carlo Risk & Distribution Analytics */}
              {mode === 'monte_carlo' && Object.keys(result.distributions).length > 0 && (
                <div style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.5rem',
                }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <BarChart2 size={20} color="var(--accent-purple)" /> Monte Carlo Empirical Risk Metrics ({numIterations} Sample Runs)
                  </h3>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                    {Object.entries(result.distributions).map(([name, dist]) => (
                      <div
                        key={name}
                        style={{
                          background: 'var(--bg-surface)',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-subtle)',
                          padding: '1rem',
                        }}
                      >
                        <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                          {name.replace(/_/g, ' ')} Distribution
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                          <div>Mean: <strong style={{ color: 'var(--text-primary)' }}>{dist.mean.toFixed(1)}</strong></div>
                          <div>Std Dev (&sigma;): <strong style={{ color: 'var(--text-primary)' }}>{dist.std.toFixed(1)}</strong></div>
                          <div>Median (p50): <strong style={{ color: 'var(--text-primary)' }}>{dist.median.toFixed(1)}</strong></div>
                          <div>95% VaR (p5): <strong style={{ color: '#f43f5e' }}>{dist.p5.toFixed(1)}</strong></div>
                          <div>95% CVaR (Tail): <strong style={{ color: '#f43f5e' }}>{dist.cvar_95 ? dist.cvar_95.toFixed(1) : '—'}</strong></div>
                          <div>Upper (p95): <strong style={{ color: '#34d399' }}>{dist.p95.toFixed(1)}</strong></div>
                        </div>

                        {/* Simulated Visual Histogram Bar */}
                        <div style={{ marginTop: '0.75rem', height: '8px', background: 'var(--bg-elevated)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                          <div style={{ width: '15%', background: '#f43f5e' }} title="Downside Tail (p5)" />
                          <div style={{ width: '70%', background: '#3b82f6' }} title="Interquartile Range" />
                          <div style={{ width: '15%', background: '#10b981' }} title="Upside (p95)" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Execution Trace Explanations */}
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
              }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} color="var(--accent-emerald)" /> Grounded Execution Trace &amp; Audit Trail
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                  {result.traces.map((trace, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '0.5rem 0.75rem',
                        borderRadius: '4px',
                        background: 'var(--bg-surface)',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      Step {trace.step_index}: <strong style={{ color: '#60a5fa' }}>{trace.variable_name}</strong> = {trace.output_value.toFixed(2)} via [{trace.formula_or_model}]
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

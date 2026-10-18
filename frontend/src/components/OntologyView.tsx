import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Search, 
  Sliders, 
  ArrowRight, 
  GitCommit, 
  Calculator, 
  ArrowUpRight, 
  ArrowDownRight,
  ShieldAlert,
  Layers,
  Sparkles
} from 'lucide-react';
import { OntologyGraph, EntityNode, RelationshipEdge, fetchOntology, fetchDAGImpact } from '../api';

interface OntologyViewProps {
  initialOntology: OntologyGraph | null;
}

export const OntologyView: React.FC<OntologyViewProps> = ({ initialOntology }) => {
  const [ontology, setOntology] = useState<OntologyGraph | null>(initialOntology);
  const [search, setSearch] = useState('');
  const [selectedNode, setSelectedNode] = useState<EntityNode | null>(null);
  const [impactData, setImpactData] = useState<{ upstream: string[]; downstream: string[] } | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  useEffect(() => {
    if (!ontology) {
      fetchOntology().then(setOntology).catch(console.error);
    }
  }, [ontology]);

  useEffect(() => {
    if (selectedNode) {
      fetchDAGImpact(selectedNode.name)
        .then((res) => {
          setImpactData({
            upstream: res.upstream_drivers || [],
            downstream: res.downstream_impacted || [],
          });
        })
        .catch(() => setImpactData(null));
    } else {
      setImpactData(null);
    }
  }, [selectedNode]);

  if (!ontology) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading enterprise ontology...
      </div>
    );
  }

  const nodesList = Object.values(ontology.nodes);
  const filteredNodes = nodesList.filter((n) => {
    const matchesSearch = n.name.toLowerCase().includes(search.toLowerCase()) || 
                          (n.description && n.description.toLowerCase().includes(search.toLowerCase()));
    const matchesType = filterType === 'ALL' || n.entity_type.toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const getNodeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'decision_lever': return '#3b82f6';
      case 'metric': return '#10b981';
      case 'asset': return '#f59e0b';
      case 'dimension': return '#8b5cf6';
      default: return '#64748b';
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Network size={24} color="var(--accent-blue)" /> Business Semantic Ontology &amp; DAG
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Inspect calculation edges, causal hypotheses, upstream parameter drivers, and downstream outcome impact.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="badge badge-blue">Version {ontology.version}</span>
          <span className="badge badge-emerald">{nodesList.length} Concepts</span>
          <span className="badge badge-purple">{ontology.edges.length} Directed Edges</span>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-card)',
        padding: '0.75rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        marginBottom: '1.5rem',
        gap: '1rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, maxWidth: '400px' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search variables or formulas..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', border: 'none', background: 'transparent', padding: '0.25rem' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Filter:</span>
          {['ALL', 'DECISION_LEVER', 'METRIC', 'ASSET', 'DIMENSION'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              style={{
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: filterType === t ? 'var(--accent-blue)' : 'var(--bg-surface)',
                color: filterType === t ? '#ffffff' : 'var(--text-secondary)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Graph Grid & Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.5rem' }}>
        {/* Nodes Grid Canvas */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '1.5rem',
          minHeight: '600px',
        }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>Discovered Concepts ({filteredNodes.length})</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click node to inspect upstream/downstream DAG paths</span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '1rem',
          }}>
            {filteredNodes.map((node) => {
              const isSelected = selectedNode?.name === node.name;
              const color = getNodeColor(node.entity_type);
              return (
                <div
                  key={node.name}
                  onClick={() => setSelectedNode(node)}
                  style={{
                    padding: '1rem',
                    borderRadius: 'var(--radius-sm)',
                    background: isSelected ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                    border: isSelected ? `2px solid ${color}` : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? `0 0 16px ${color}25` : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      color: isSelected ? '#ffffff' : 'var(--text-primary)',
                      fontFamily: 'var(--font-mono)',
                    }}>
                      {node.name}
                    </span>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        padding: '0.15rem 0.5rem',
                        borderRadius: 'var(--radius-full)',
                        background: `${color}15`,
                        color: color,
                        border: `1px solid ${color}30`,
                      }}
                    >
                      {node.entity_type.replace('_', ' ')}
                    </span>
                  </div>

                  {node.formula && (
                    <div style={{
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      color: '#93c5fd',
                      background: 'rgba(37, 99, 235, 0.1)',
                      padding: '0.35rem 0.5rem',
                      borderRadius: '4px',
                      marginBottom: '0.5rem',
                    }}>
                      = {node.formula}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>Unit: <strong style={{ color: 'var(--text-secondary)' }}>{node.unit || '—'}</strong></span>
                    {node.source_table && (
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>
                        {node.source_table.split('.').pop()}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Inspector Panel */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}>
          {selectedNode ? (
            <>
              <div>
                <span className="badge badge-blue" style={{ marginBottom: '0.5rem' }}>
                  {selectedNode.entity_type.replace('_', ' ')}
                </span>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginBottom: '0.25rem' }}>
                  {selectedNode.name}
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {selectedNode.description || 'Discovered ontology entity'}
                </p>
              </div>

              {selectedNode.formula && (
                <div style={{
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    Calculation AST Formula
                  </div>
                  <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: '#60a5fa' }}>
                    {selectedNode.formula}
                  </div>
                </div>
              )}

              {/* Upstream Influencers / Ancestors */}
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.5rem',
                  color: 'var(--text-secondary)',
                }}>
                  <ArrowUpRight size={16} color="var(--accent-blue)" /> Upstream Drivers ({impactData?.upstream.length || 0})
                </div>
                {impactData && impactData.upstream.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {impactData.upstream.map((up) => (
                      <span
                        key={up}
                        onClick={() => {
                          const n = ontology.nodes[up];
                          if (n) setSelectedNode(n);
                        }}
                        className="badge badge-blue font-mono"
                        style={{ cursor: 'pointer' }}
                      >
                        {up}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Root decision lever / parameter</span>
                )}
              </div>

              {/* Downstream Impact / Descendants */}
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginBottom: '0.5rem',
                  color: 'var(--text-secondary)',
                }}>
                  <ArrowDownRight size={16} color="var(--accent-emerald)" /> Downstream Impact ({impactData?.downstream.length || 0})
                </div>
                {impactData && impactData.downstream.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {impactData.downstream.map((down) => (
                      <span
                        key={down}
                        onClick={() => {
                          const n = ontology.nodes[down];
                          if (n) setSelectedNode(n);
                        }}
                        className="badge badge-emerald font-mono"
                        style={{ cursor: 'pointer' }}
                      >
                        {down}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Leaf outcome metric</span>
                )}
              </div>

              {/* Invariants & Bounds */}
              <div style={{
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                fontSize: '0.775rem',
              }}>
                <div style={{ fontWeight: 600, color: '#34d399', marginBottom: '0.25rem' }}>
                  Domain Operating Invariants
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>
                  Min Bound: {selectedNode.min_bound !== null && selectedNode.min_bound !== undefined ? selectedNode.min_bound : 'None'}<br/>
                  Max Bound: {selectedNode.max_bound !== null && selectedNode.max_bound !== undefined ? selectedNode.max_bound : 'None'}<br/>
                  Verified Acyclic in Calculation DAG
                </div>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              <Layers size={32} style={{ marginBottom: '0.75rem', opacity: 0.5 }} />
              <div style={{ fontWeight: 600 }}>No Node Selected</div>
              <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Select any concept node to inspect its DAG dependencies and downstream impact.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

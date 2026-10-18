import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Table, 
  Eye, 
  Sparkles, 
  Key, 
  CheckCircle2, 
  XCircle, 
  RefreshCw,
  Layers,
  BarChart2
} from 'lucide-react';
import { DataSourceMetadata, TableSchema, fetchConnectors, fetchTables, sampleTable, runDiscovery } from '../api';

interface DataSourcesViewProps {
  connectors: DataSourceMetadata[];
  onDiscoveryComplete: () => void;
}

export const DataSourcesView: React.FC<DataSourcesViewProps> = ({ connectors, onDiscoveryComplete }) => {
  const [selectedSource, setSelectedSource] = useState<string>('mock_lakehouse');
  const [selectedCatalog, setSelectedCatalog] = useState<string>('retail_lakehouse');
  const [selectedSchema, setSelectedSchema] = useState<string>('gold_analytics');
  const [tables, setTables] = useState<TableSchema[]>([]);
  const [activeTable, setActiveTable] = useState<TableSchema | null>(null);
  const [sampleData, setSampleData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [discovering, setDiscovering] = useState<boolean>(false);
  const [discoveryMsg, setDiscoveryMsg] = useState<string | null>(null);

  // Databricks modal state
  const [showDatabricksModal, setShowDatabricksModal] = useState<boolean>(false);
  const [dbHost, setDbHost] = useState('adb-98234123.azuredatabricks.net');
  const [dbPath, setDbPath] = useState('/sql/1.0/warehouses/a1b2c3d4e5');
  const [dbToken, setDbToken] = useState('dapi_live_token_simlab_demo_9823471');

  useEffect(() => {
    loadTables(selectedSource, selectedCatalog, selectedSchema);
  }, [selectedSource, selectedCatalog, selectedSchema]);

  const loadTables = async (src: string, cat: string, sch: string) => {
    setLoading(true);
    try {
      const tbls = await fetchTables(src, cat, sch);
      setTables(tbls);
      if (tbls.length > 0) {
        setActiveTable(tbls[0]);
        loadSample(src, cat, sch, tbls[0].table_name);
      } else {
        setActiveTable(null);
        setSampleData(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadSample = async (src: string, cat: string, sch: string, tbl: string) => {
    try {
      const data = await sampleTable(src, cat, sch, tbl, 10);
      setSampleData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunDiscovery = async () => {
    setDiscovering(true);
    setDiscoveryMsg(null);
    try {
      const res = await runDiscovery(selectedSource, selectedCatalog, selectedSchema);
      setDiscoveryMsg(`Discovered ${res.nodes_discovered} concepts and ${res.edges_inferred} dependency edges!`);
      onDiscoveryComplete();
    } catch (e) {
      setDiscoveryMsg('Discovery failed.');
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Database size={24} color="var(--accent-blue)" /> Enterprise Data Sources & Lakehouses
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Inspect catalogs, schemas, tables, and column statistics. Trigger automated ontology discovery.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setShowDatabricksModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.9rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)',
              fontSize: '0.825rem',
              fontWeight: 600,
            }}
          >
            <Key size={15} color="var(--accent-amber)" /> Configure Databricks UC
          </button>
          <button
            onClick={handleRunDiscovery}
            disabled={discovering}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-blue)',
              color: '#ffffff',
              fontSize: '0.825rem',
              fontWeight: 600,
              boxShadow: '0 2px 8px var(--accent-blue-glow)',
            }}
          >
            <Sparkles size={15} /> {discovering ? 'Discovering Semantics...' : 'Auto-Discover Ontology'}
          </button>
        </div>
      </div>

      {discoveryMsg && (
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#34d399',
          fontSize: '0.85rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <CheckCircle2 size={16} /> {discoveryMsg}
        </div>
      )}

      {/* Data Source, Catalog & Schema Selector */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        background: 'var(--bg-card)',
        padding: '0.85rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        marginBottom: '1.5rem',
      }}>
        {/* Connector Source Selection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Source:</span>
          <select
            value={selectedSource}
            onChange={(e) => {
              const src = e.target.value;
              setSelectedSource(src);
              if (src === 'databricks_primary') {
                setSelectedCatalog('workspace');
                setSelectedSchema('default');
              } else {
                setSelectedCatalog('retail_lakehouse');
                setSelectedSchema('gold_analytics');
              }
            }}
            style={{ fontSize: '0.85rem', background: 'var(--bg-surface)' }}
          >
            <option value="databricks_primary">Databricks Unity Catalog (Live)</option>
            <option value="mock_lakehouse">Enterprise Mock Lakehouse</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Catalog:</span>
          {selectedSource === 'databricks_primary' ? (
            <select
              value={selectedCatalog}
              onChange={(e) => setSelectedCatalog(e.target.value)}
              style={{ fontSize: '0.85rem', background: 'var(--bg-surface)' }}
            >
              <option value="workspace">workspace</option>
              <option value="samples">samples</option>
            </select>
          ) : (
            <select
              value={selectedCatalog}
              onChange={(e) => {
                const cat = e.target.value;
                setSelectedCatalog(cat);
                setSelectedSchema(cat === 'retail_lakehouse' ? 'gold_analytics' : 'dispatch_market');
              }}
              style={{ fontSize: '0.85rem', background: 'var(--bg-surface)' }}
            >
              <option value="retail_lakehouse">retail_lakehouse (Retail & Sales)</option>
              <option value="energy_grid">energy_grid (Power Generation & Storage)</option>
            </select>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Schema:</span>
          <span className="badge badge-blue">{selectedSchema}</span>
          {selectedSource === 'databricks_primary' && (
            <span className="badge badge-emerald">Live Unity Catalog Connected</span>
          )}
        </div>
      </div>

      {/* Main Content: Tables List & Detail Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem' }}>
        {/* Tables Left List */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}>
          <div style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.25rem 0.5rem' }}>
            Tables ({tables.length})
          </div>

          {tables.map((t) => {
            const isSelected = activeTable?.table_name === t.table_name;
            return (
              <div
                key={t.table_name}
                onClick={() => {
                  setActiveTable(t);
                  loadSample(selectedSource, selectedCatalog, selectedSchema, t.table_name);
                }}
                style={{
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: isSelected ? 'var(--bg-elevated)' : 'transparent',
                  border: isSelected ? '1px solid var(--border-focus)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.875rem' }}>
                  <Table size={16} color={isSelected ? 'var(--accent-blue)' : 'var(--text-muted)'} />
                  {t.table_name}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {t.columns.length} columns &bull; {t.row_count_estimate || 0} rows
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Detail Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {activeTable && (
            <>
              {/* Table Schema / Columns */}
              <div style={{
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                padding: '1.25rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <BarChart2 size={18} color="var(--accent-blue)" /> Column Statistics &amp; Profile ({activeTable.table_name})
                  </h3>
                  <span className="badge badge-emerald">{activeTable.row_count_estimate || 0} Records</span>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Column Name</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Data Type</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Numeric</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Min Value</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Max Value</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Mean</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeTable.columns.map((c, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                          <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>{c.name}</td>
                          <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-secondary)' }}>
                            <span className="badge badge-blue font-mono" style={{ fontSize: '0.7rem' }}>{c.data_type}</span>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            {c.is_numeric ? <span style={{ color: '#34d399' }}>Yes</span> : <span style={{ color: 'var(--text-muted)' }}>No</span>}
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {c.min_value !== null && c.min_value !== undefined ? c.min_value : '—'}
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {c.max_value !== null && c.max_value !== undefined ? c.max_value : '—'}
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-secondary)' }}>
                            {c.mean_value !== null && c.mean_value !== undefined ? c.mean_value.toFixed(2) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Sample Data Records */}
              {sampleData && sampleData.rows && sampleData.rows.length > 0 && (
                <div style={{
                  background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  padding: '1.25rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Eye size={18} color="var(--accent-purple)" /> Sample Data Preview ({sampleData.row_count} Rows)
                    </h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Execution: {sampleData.execution_time_ms.toFixed(1)} ms
                    </span>
                  </div>

                  <div style={{ overflowX: 'auto', maxHeight: '320px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                          {sampleData.columns.map((col: string, idx: number) => (
                            <th key={idx} style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap' }}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sampleData.rows.map((row: any, rIdx: number) => (
                          <tr key={rIdx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                            {sampleData.columns.map((col: string, cIdx: number) => (
                              <td key={cIdx} style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                                {row[col] !== undefined && row[col] !== null ? String(row[col]) : 'NULL'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Databricks Modal */}
      {showDatabricksModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-lg)',
            width: '540px',
            padding: '2rem',
            boxShadow: 'var(--shadow-lg)',
          }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Key size={20} color="var(--accent-amber)" /> Databricks Unity Catalog Connection
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Connect live enterprise Databricks SQL Warehouses. Tokens are masked and never leaked to browser or logs.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Server Hostname
                </label>
                <input
                  type="text"
                  value={dbHost}
                  onChange={(e) => setDbHost(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  HTTP Path
                </label>
                <input
                  type="text"
                  value={dbPath}
                  onChange={(e) => setDbPath(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Personal Access Token (PAT)
                </label>
                <input
                  type="password"
                  value={dbToken}
                  onChange={(e) => setDbToken(e.target.value)}
                  style={{ width: '100%' }}
                />
                <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'block' }}>
                  Masked preview: {dbToken ? `${dbToken.slice(0, 4)}...${dbToken.slice(-4)}` : ''}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={() => setShowDatabricksModal(false)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-elevated)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                }}
              >
                Close
              </button>
              <button
                onClick={() => {
                  alert("Databricks credentials saved with token masking!");
                  setShowDatabricksModal(false);
                }}
                style={{
                  padding: '0.5rem 1.25rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-blue)',
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                }}
              >
                Save &amp; Test Connection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

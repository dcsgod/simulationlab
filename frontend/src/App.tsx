import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { DataSourcesView } from './components/DataSourcesView';
import { OntologyView } from './components/OntologyView';
import { SimulationStudioView } from './components/SimulationStudioView';
import { OptimizationWorkspaceView } from './components/OptimizationWorkspaceView';
import { CopilotView } from './components/CopilotView';
import { 
  HealthStatus, 
  DataSourceMetadata, 
  OntologyGraph, 
  fetchHealth, 
  fetchConnectors, 
  fetchOntology 
} from './api';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [connectors, setConnectors] = useState<DataSourceMetadata[]>([]);
  const [ontology, setOntology] = useState<OntologyGraph | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(console.error);
    fetchConnectors().then(setConnectors).catch(console.error);
    fetchOntology().then(setOntology).catch(console.error);
  }, []);

  const refreshOntology = () => {
    fetchOntology().then(setOntology).catch(console.error);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} health={health} />
      
      <main style={{ flex: 1, paddingBottom: '3rem' }}>
        {activeTab === 'dashboard' && (
          <DashboardView
            ontology={ontology}
            connectors={connectors}
            setActiveTab={setActiveTab}
          />
        )}
        {activeTab === 'data' && (
          <DataSourcesView
            connectors={connectors}
            onDiscoveryComplete={refreshOntology}
          />
        )}
        {activeTab === 'ontology' && (
          <OntologyView initialOntology={ontology} />
        )}
        {activeTab === 'simulations' && (
          <SimulationStudioView />
        )}
        {activeTab === 'optimization' && (
          <OptimizationWorkspaceView />
        )}
        {activeTab === 'copilot' && (
          <CopilotView />
        )}
      </main>
    </div>
  );
}

export default App;

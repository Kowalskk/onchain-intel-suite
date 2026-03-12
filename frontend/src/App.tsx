import React, { useState } from 'react';
import { useTrace } from './hooks/useTrace';
import { SearchBar } from './components/SearchBar';
import { FilterPanel } from './components/FilterPanel';
import { FlowList } from './components/FlowList';
import { GraphVisualization } from './components/GraphVisualization';
import { ThemeToggle } from './components/ThemeToggle';

function App() {
  const {
    address,
    graph,
    flows,
    tokens,
    filters,
    setFilters,
    isLoading,
    error,
    trace,
  } = useTrace();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const handleSearch = (addr: string) => {
    setSelectedNodeId(null);
    trace(addr);
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      padding: '16px',
      gap: '16px',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 24px',
        background: 'var(--sol-bg-secondary)',
        border: '1px solid var(--sol-border)',
        borderRadius: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <h1 style={{
            margin: 0,
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--sol-cyan)',
            letterSpacing: '0.05em',
          }}>
            SOLARIZED
          </h1>
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <main style={{
        display: 'flex',
        flex: 1,
        gap: '16px',
        minHeight: 0, // important for flex children scrolling
      }}>
        {/* Left Sidebar: Filters & Flow List */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          width: '280px',
          flexShrink: 0,
        }}>
          <FilterPanel
            filters={filters}
            onFiltersChange={setFilters}
            availableTokens={tokens}
            isLoading={isLoading}
          />
          {flows && (
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <FlowList
                inflows={flows.inflows}
                outflows={flows.outflows}
                onAddressClick={handleSearch}
              />
            </div>
          )}
        </div>

        {/* Center/Right: Graph Visualization */}
        <div style={{
          flex: 1,
          background: 'var(--sol-bg-secondary)',
          border: '1px solid var(--sol-border)',
          borderRadius: '12px',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {error ? (
            <div style={{ color: 'var(--sol-red)', fontFamily: 'JetBrains Mono, monospace' }}>
              Error: {error}
            </div>
          ) : graph ? (
            <GraphVisualization
              graph={graph}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedNodeId}
            />
          ) : (
            <div style={{
              color: 'var(--sol-text-secondary)',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '14px',
              textAlign: 'center',
            }}>
              {isLoading ? 'TRACING...' : 'ENTER A WALLET ADDRESS TO BEGIN'}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

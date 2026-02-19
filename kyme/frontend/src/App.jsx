import React, { useEffect, useState } from 'react';
import { useEditorStore } from './store/useEditorStore.js';
import { FileTree } from './components/FileTree.jsx';
import { PropertyEditor } from './components/PropertyEditor.jsx';
import { GitHubModal } from './components/GitHubModal.jsx';
import { GraphCanvas } from './components/GraphCanvas.jsx';

function App() {
  const {
    graph,
    selectedNodeId,
    selectedFile,
    selectNode,
    selectFile,
    updateNodePosition,
    isAuthenticated,
    checkAuth,
    loadRepositories,
    validate,
    validationErrors,
    applyChanges,
    getNodesForFile,
    getDirtyFiles,
    sidebarOpen,
    toggleSidebar,
  } = useEditorStore();

  const [showGitHubModal, setShowGitHubModal] = useState(false);
  const [particleOffset, setParticleOffset] = useState(0);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [createPR, setCreatePR] = useState(true);
  const [applying, setApplying] = useState(false);

  // Particle animation
  useEffect(() => {
    const interval = setInterval(() => {
      setParticleOffset(prev => (prev + 2) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const selectedNode = graph?.nodes.find(n => n.id === selectedNodeId) || null;
  const dirtyFiles = getDirtyFiles();

  const handleApply = async () => {
    if (!commitMessage.trim()) return;
    setApplying(true);
    try {
      await applyChanges(commitMessage, createPR);
      setShowApplyModal(false);
      setCommitMessage('');
    } catch (err) {
      console.error('Failed to apply changes:', err);
    } finally {
      setApplying(false);
    }
  };

  const errorCount = validationErrors.filter(e => e.severity === 'error').length;
  const warningCount = validationErrors.filter(e => e.severity === 'warning').length;

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: '#0a0a0c',
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Header */}
      <header style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '50px',
        background: '#1a1a2e',
        borderBottom: '2px solid #2a2a3e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={toggleSidebar}
            style={{
              background: 'none',
              border: 'none',
              color: '#888',
              cursor: 'pointer',
              fontSize: '18px',
              padding: '4px',
            }}
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
          <h1 style={{
            margin: 0,
            fontSize: '16px',
            color: '#00ff00',
            fontFamily: 'monospace',
          }}>
            Kubernetes YAML-Manifest Visualizer & Editor UI
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Validation status */}
          {(errorCount > 0 || warningCount > 0) && (
            <div style={{
              display: 'flex',
              gap: '8px',
              padding: '4px 8px',
              background: '#2a2a3e',
              borderRadius: '4px',
            }}>
              {errorCount > 0 && (
                <span style={{ color: '#ff6b6b', fontSize: '12px' }}>
                  ⛔ {errorCount}
                </span>
              )}
              {warningCount > 0 && (
                <span style={{ color: '#ffd93d', fontSize: '12px' }}>
                  ⚠️ {warningCount}
                </span>
              )}
            </div>
          )}

          {/* Apply button */}
          {dirtyFiles.length > 0 && (
            <button
              onClick={() => setShowApplyModal(true)}
              style={{
                padding: '8px 16px',
                background: '#00ff00',
                border: 'none',
                borderRadius: '4px',
                color: '#0a0a0c',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 'bold',
              }}
            >
              Apply Changes ({dirtyFiles.length})
            </button>
          )}

          {/* GitHub button */}
          <button
            onClick={() => {
              if (!isAuthenticated) {
                setShowGitHubModal(true);
              } else {
                loadRepositories();
                setShowGitHubModal(true);
              }
            }}
            style={{
              padding: '8px 16px',
              background: isAuthenticated ? '#24292e' : '#4a4a6a',
              border: '1px solid #4a4a6a',
              borderRadius: '4px',
              color: '#e0e0e0',
              cursor: 'pointer',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            📂 {isAuthenticated ? 'Change Repo' : 'Connect GitHub'}
          </button>
        </div>
      </header>

      {/* Sidebar */}
      {sidebarOpen && (
        <aside style={{
          position: 'absolute',
          left: 0,
          top: '50px',
          bottom: 0,
          width: '250px',
          background: '#12121a',
          borderRight: '2px solid #2a2a3e',
          overflow: 'auto',
          zIndex: 90,
        }}>
          <div style={{ padding: '12px', borderBottom: '1px solid #2a2a3e' }}>
            <h3 style={{ margin: 0, color: '#888', fontSize: '11px', textTransform: 'uppercase' }}>
              Files
            </h3>
          </div>
          <FileTree onSelectFile={selectFile} />
        </aside>
      )}

      {/* Main Canvas */}
      <main style={{
        position: 'absolute',
        top: '50px',
        left: sidebarOpen ? '250px' : '0',
        right: selectedNode ? '350px' : '0',
        bottom: 0,
      }}>
        {!graph || graph.nodes.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            flexDirection: 'column',
            gap: '16px',
          }}>
            <p style={{ color: '#666', fontSize: '14px' }}>
              No manifests loaded
            </p>
            <button
              onClick={() => setShowGitHubModal(true)}
              style={{
                padding: '12px 24px',
                background: '#00ff00',
                border: 'none',
                borderRadius: '4px',
                color: '#0a0a0c',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
              }}
            >
              Connect GitHub to Load Manifests
            </button>
          </div>
        ) : (
          <GraphCanvas
            nodes={graph.nodes.filter(n => !selectedFile || n.filePath === selectedFile)}
            edges={graph.edges}
            selectedNodeId={selectedNodeId}
            onSelectNode={selectNode}
            onNodeMove={updateNodePosition}
            hoveredNodeId={hoveredNodeId}
            onHoverNode={setHoveredNodeId}
            particleOffset={particleOffset}
          />
        )}
      </main>

      {/* Property Editor */}
      {selectedNode && (
        <PropertyEditor
          node={selectedNode}
          onClose={() => selectNode(null)}
        />
      )}

      {/* GitHub Modal */}
      {showGitHubModal && (
        <GitHubModal onClose={() => setShowGitHubModal(false)} />
      )}

      {/* Apply Changes Modal */}
      {showApplyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            background: '#1a1a2e',
            borderRadius: '8px',
            padding: '24px',
            width: '450px',
          }}>
            <h2 style={{ margin: '0 0 16px', color: '#00ff00', fontSize: '18px' }}>
              Apply Changes
            </h2>
            
            <p style={{ color: '#888', fontSize: '12px', marginBottom: '16px' }}>
              This will update {dirtyFiles.length} file(s) in your repository.
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', color: '#888', fontSize: '12px', marginBottom: '8px' }}>
                Commit Message
              </label>
              <input
                type="text"
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                placeholder="Describe your changes..."
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a3e',
                  border: '1px solid #4a4a6a',
                  color: '#e0e0e0',
                  borderRadius: '4px',
                  fontSize: '13px',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={createPR}
                  onChange={(e) => setCreatePR(e.target.checked)}
                  style={{ width: '16px', height: '16px' }}
                />
                <span style={{ color: '#e0e0e0', fontSize: '13px' }}>
                  Create Pull Request (recommended)
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleApply}
                disabled={!commitMessage.trim() || applying}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#00ff00',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#0a0a0c',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  opacity: !commitMessage.trim() || applying ? 0.5 : 1,
                }}
              >
                {applying ? 'Applying...' : 'Apply Changes'}
              </button>
              <button
                onClick={() => setShowApplyModal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#4a4a6a',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#e0e0e0',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

import React, { useState } from 'react';
import { useEditorStore } from '../store/useEditorStore.js';

export const GitHubModal = ({ onClose }) => {
  const {
    isAuthenticated,
    user,
    repositories,
    loadRepositories,
    loadFromGitHub,
    authenticate,
    selectedRepo,
    selectedBranch,
  } = useEditorStore();

  const [selectedRepoState, setSelectedRepoState] = useState('');
  const [branch, setBranch] = useState('main');
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleConnect = () => {
    authenticate();
  };

  const handleRepoSelect = async (repoFullName) => {
    setSelectedRepoState(repoFullName);
    setLoading(true);
    try {
      const { branches: repoBranches } = await fetch(`/api/repos/${encodeURIComponent(repoFullName)}/branches`).then(r => r.json());
      setBranches(repoBranches);
      if (repoBranches.length > 0) {
        setBranch(repoBranches[0]);
      }
    } catch (err) {
      console.error('Failed to load branches:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoad = () => {
    if (selectedRepoState && branch) {
      loadFromGitHub(selectedRepoState, branch, '');
      onClose();
    }
  };

  return (
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
        width: '500px',
        maxHeight: '80vh',
        overflow: 'auto',
      }}>
        <h2 style={{ margin: '0 0 16px', color: '#00ff00', fontSize: '18px' }}>
          Connect to GitHub
        </h2>

        {!isAuthenticated ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p style={{ color: '#888', marginBottom: '16px' }}>
              Connect your GitHub account to load and edit Kubernetes manifests
            </p>
            <button
              onClick={handleConnect}
              style={{
                padding: '12px 24px',
                background: '#24292e',
                border: '1px solid #4a4a6a',
                color: '#e0e0e0',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                margin: '0 auto',
              }}
            >
              <span>🔗</span> Connect with GitHub
            </button>
          </div>
        ) : (
          <>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              background: '#2a2a3e',
              borderRadius: '6px',
              marginBottom: '16px',
            }}>
              {user?.avatar && (
                <img
                  src={user.avatar}
                  alt={user.login}
                  style={{ width: '32px', height: '32px', borderRadius: '50%' }}
                />
              )}
              <span style={{ color: '#e0e0e0' }}>Connected as {user?.login}</span>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', color: '#888', fontSize: '12px', marginBottom: '8px' }}>
                Select Repository
              </label>
              <select
                value={selectedRepoState}
                onChange={(e) => handleRepoSelect(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a3e',
                  border: '1px solid #4a4a6a',
                  color: '#e0e0e0',
                  borderRadius: '4px',
                  fontSize: '13px',
                }}
              >
                <option value="">-- Select a repository --</option>
                {repositories.map(repo => (
                  <option key={repo.fullName} value={repo.fullName}>
                    {repo.fullName} {repo.private ? '🔒' : ''}
                  </option>
                ))}
              </select>
            </div>

            {selectedRepoState && (
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', color: '#888', fontSize: '12px', marginBottom: '8px' }}>
                  Select Branch
                </label>
                <select
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  disabled={loading}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: '#2a2a3e',
                    border: '1px solid #4a4a6a',
                    color: '#e0e0e0',
                    borderRadius: '4px',
                    fontSize: '13px',
                  }}
                >
                  {loading ? (
                    <option>Loading...</option>
                  ) : (
                    branches.map(b => (
                      <option key={b} value={b}>{b}</option>
                    ))
                  )}
                </select>
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', marginTop: '20px' }}>
              <button
                onClick={handleLoad}
                disabled={!selectedRepoState || !branch}
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
                  opacity: !selectedRepoState || !branch ? 0.5 : 1,
                }}
              >
                Load Manifests
              </button>
              <button
                onClick={onClose}
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
          </>
        )}
      </div>
    </div>
  );
};

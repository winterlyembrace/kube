import React, { useState } from 'react';
import { useEditorStore } from '../store/useEditorStore.js';

export const PropertyEditor = ({ node, onClose }) => {
  const { updateNode, validationErrors } = useEditorStore();
  const [localNode, setLocalNode] = useState({ ...node });
  const [activeTab, setActiveTab] = useState('basic');

  const nodeErrors = validationErrors.filter(e => e.nodeId === node.id);

  const handleChange = (field, value) => {
    const updated = { ...localNode, [field]: value };
    setLocalNode(updated);
  };

  const handleSave = async () => {
    const updates = {};

    if (localNode.name !== node.name) updates.name = localNode.name;
    if (localNode.namespace !== node.namespace) updates.namespace = localNode.namespace;
    if (JSON.stringify(localNode.labels) !== JSON.stringify(node.labels)) {
      updates.labels = localNode.labels;
    }
    if (localNode.replicas !== node.replicas) updates.replicas = localNode.replicas;
    if (localNode.serviceType !== node.serviceType) updates.serviceType = localNode.serviceType;
    if (localNode.selector && JSON.stringify(localNode.selector) !== JSON.stringify(node.selector)) {
      updates.selector = localNode.selector;
    }
    if (localNode.containers && JSON.stringify(localNode.containers) !== JSON.stringify(node.containers)) {
      updates.containers = localNode.containers;
    }
    if (localNode.ports && JSON.stringify(localNode.ports) !== JSON.stringify(node.ports)) {
      updates.ports = localNode.ports;
    }

    if (Object.keys(updates).length > 0) {
      await updateNode(node.id, updates);
    }
    onClose();
  };

  const getFieldValue = (field) => {
    return localNode[field];
  };

  return (
    <div style={{
      position: 'absolute',
      right: 0,
      top: 0,
      bottom: 0,
      width: '350px',
      background: '#1a1a2e',
      borderLeft: '2px solid #4a4a6a',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #3a3a5a',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <h3 style={{ margin: 0, color: '#00ff00', fontSize: '14px' }}>
            {node.kind}: {node.name}
          </h3>
          <span style={{ fontSize: '10px', color: '#888' }}>{node.filePath}</span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#888',
            cursor: 'pointer',
            fontSize: '18px',
          }}
        >
          ✕
        </button>
      </div>

      {/* Validation Errors */}
      {nodeErrors.length > 0 && (
        <div style={{
          padding: '12px 16px',
          background: '#2a1a1a',
          borderBottom: '1px solid #4a2a2a',
        }}>
          {nodeErrors.map((error, i) => (
            <div key={i} style={{
              color: error.severity === 'error' ? '#ff6b6b' : '#ffd93d',
              fontSize: '11px',
              marginBottom: '4px',
            }}>
              {error.severity === 'error' ? '⛔' : '⚠️'} {error.message}
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #3a3a5a',
      }}>
        {['basic', 'spec', 'labels'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1,
              padding: '10px',
              background: activeTab === tab ? '#2a2a3e' : 'transparent',
              border: 'none',
              color: activeTab === tab ? '#00ff00' : '#888',
              cursor: 'pointer',
              fontSize: '11px',
              textTransform: 'uppercase',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
        {activeTab === 'basic' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <FormField
              label="Name"
              value={getFieldValue('name')}
              onChange={(v) => handleChange('name', v)}
            />
            <FormField
              label="Namespace"
              value={getFieldValue('namespace')}
              onChange={(v) => handleChange('namespace', v)}
            />
            {node.kind === 'Deployment' && (
              <FormField
                label="Replicas"
                type="number"
                value={String(getFieldValue('replicas') || 1)}
                onChange={(v) => handleChange('replicas', parseInt(v) || 1)}
              />
            )}
            {node.kind === 'Service' && (
              <FormField
                label="Type"
                type="select"
                value={getFieldValue('serviceType') || 'ClusterIP'}
                options={['ClusterIP', 'NodePort', 'LoadBalancer']}
                onChange={(v) => handleChange('serviceType', v)}
              />
            )}
          </div>
        )}

        {activeTab === 'spec' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {node.kind === 'Deployment' && node.containers?.map((container, idx) => (
              <div key={idx} style={{
                background: '#2a2a3e',
                padding: '12px',
                borderRadius: '4px',
              }}>
                <div style={{ color: '#00ff00', fontSize: '11px', marginBottom: '8px' }}>
                  Container {idx + 1}
                </div>
                <FormField
                  label="Name"
                  value={container.name}
                  onChange={(v) => {
                    const containers = [...(node.containers || [])];
                    containers[idx].name = v;
                    handleChange('containers', containers);
                  }}
                />
                <FormField
                  label="Image"
                  value={container.image}
                  onChange={(v) => {
                    const containers = [...(node.containers || [])];
                    containers[idx].image = v;
                    handleChange('containers', containers);
                  }}
                />
              </div>
            ))}
            {node.kind === 'Service' && node.ports?.map((port, idx) => (
              <div key={idx} style={{
                background: '#2a2a3e',
                padding: '12px',
                borderRadius: '4px',
              }}>
                <div style={{ color: '#00ff00', fontSize: '11px', marginBottom: '8px' }}>
                  Port {idx + 1}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="number"
                    value={port.port}
                    onChange={(e) => {
                      const ports = [...(node.ports || [])];
                      ports[idx].port = parseInt(e.target.value);
                      handleChange('ports', ports);
                    }}
                    style={{
                      width: '70px',
                      background: '#1a1a2e',
                      border: '1px solid #4a4a6a',
                      color: '#e0e0e0',
                      padding: '6px',
                      fontSize: '11px',
                    }}
                    placeholder="Port"
                  />
                  <input
                    type="number"
                    value={port.targetPort || port.port}
                    onChange={(e) => {
                      const ports = [...(node.ports || [])];
                      ports[idx].targetPort = parseInt(e.target.value);
                      handleChange('ports', ports);
                    }}
                    style={{
                      width: '70px',
                      background: '#1a1a2e',
                      border: '1px solid #4a4a6a',
                      color: '#e0e0e0',
                      padding: '6px',
                      fontSize: '11px',
                    }}
                    placeholder="Target"
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'labels' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(node.labels || {}).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="text"
                  value={key}
                  readOnly
                  style={{
                    flex: 1,
                    background: '#1a1a2e',
                    border: '1px solid #4a4a6a',
                    color: '#00ff00',
                    padding: '6px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
                <span style={{ color: '#888' }}>=</span>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => {
                    handleChange('labels', { ...node.labels, [key]: e.target.value });
                  }}
                  style={{
                    flex: 1,
                    background: '#1a1a2e',
                    border: '1px solid #4a4a6a',
                    color: '#e0e0e0',
                    padding: '6px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
              </div>
            ))}
            <button
              onClick={() => {
                const newKey = `key-${Date.now()}`;
                handleChange('labels', { ...node.labels, [newKey]: '' });
              }}
              style={{
                padding: '8px',
                background: '#2a2a3e',
                border: '1px solid #4a4a6a',
                color: '#00ff00',
                cursor: 'pointer',
                fontSize: '11px',
              }}
            >
              + Add Label
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid #3a3a5a',
        display: 'flex',
        gap: '8px',
      }}>
        <button
          onClick={handleSave}
          style={{
            flex: 1,
            padding: '10px',
            background: '#00ff00',
            border: 'none',
            borderRadius: '4px',
            color: '#0a0a0c',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: 'bold',
          }}
        >
          Save Changes
        </button>
        <button
          onClick={onClose}
          style={{
            flex: 1,
            padding: '10px',
            background: '#4a4a6a',
            border: 'none',
            borderRadius: '4px',
            color: '#e0e0e0',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

const FormField = ({ label, value, type = 'text', options, onChange }) => {
  if (type === 'select' && options) {
    return (
      <div>
        <label style={{ display: 'block', color: '#888', fontSize: '11px', marginBottom: '4px' }}>
          {label}
        </label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: '100%',
            background: '#1a1a2e',
            border: '1px solid #4a4a6a',
            color: '#e0e0e0',
            padding: '8px',
            fontSize: '11px',
          }}
        >
          {options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div>
      <label style={{ display: 'block', color: '#888', fontSize: '11px', marginBottom: '4px' }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: '100%',
          background: '#1a1a2e',
          border: '1px solid #4a4a6a',
          color: '#e0e0e0',
          padding: '8px',
          fontSize: '11px',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
};

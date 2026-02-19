import React, { useState } from 'react';
import { useEditorStore } from '../store/useEditorStore.js';

export const FileTree = ({ onSelectFile }) => {
  const { graph, selectedFile, selectFile } = useEditorStore();
  const [expandedFolders, setExpandedFolders] = useState(new Set(['']));

  if (!graph) {
    return (
      <div style={{ padding: '10px', color: '#666' }}>
        No files loaded
      </div>
    );
  }

  // Build tree structure from file paths
  const buildTree = () => {
    const root = [];
    const map = new Map();

    Object.keys(graph.files).sort().forEach(filePath => {
      const parts = filePath.split('/');
      let currentPath = '';
      let parent = root;

      parts.forEach((part, index) => {
        const prevPath = currentPath;
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!map.has(currentPath)) {
          const isFile = index === parts.length - 1;
          const node = {
            name: part,
            path: currentPath,
            type: isFile ? 'file' : 'dir',
            level: index,
            children: isFile ? undefined : []
          };
          map.set(currentPath, node);
          parent.push(node);
        }

        if (index < parts.length - 1) {
          parent = map.get(currentPath).children;
        }
      });
    });

    return root;
  };

  const toggleFolder = (path) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const renderNode = (node) => {
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    const fileInfo = graph.files[node.path];
    const isDirty = fileInfo?.dirty || false;

    if (node.type === 'file') {
      return (
        <div
          key={node.path}
          onClick={() => {
            selectFile(node.path);
            onSelectFile(node.path);
          }}
          style={{
            padding: '4px 8px',
            paddingLeft: `${node.level * 16 + 8}px`,
            cursor: 'pointer',
            background: isSelected ? '#2a2a3e' : 'transparent',
            color: isDirty ? '#ff6b6b' : '#e0e0e0',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span style={{ fontSize: '12px' }}>
            {node.name.endsWith('.yaml') || node.name.endsWith('.yml') ? '📄' : '📋'}
          </span>
          <span style={{ fontSize: '11px', fontFamily: 'monospace' }}>
            {node.name}
            {isDirty && <span style={{ color: '#ff6b6b', marginLeft: '4px' }}>●</span>}
          </span>
        </div>
      );
    }

    return (
      <div key={node.path}>
        <div
          onClick={() => toggleFolder(node.path)}
          style={{
            padding: '4px 8px',
            paddingLeft: `${node.level * 16 + 8}px`,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#b0b0b0',
          }}
        >
          <span style={{ fontSize: '10px' }}>
            {isExpanded ? '▼' : '▶'}
          </span>
          <span style={{ fontSize: '12px' }}>📁</span>
          <span style={{ fontSize: '11px', fontFamily: 'monospace' }}>{node.name}</span>
        </div>
        {isExpanded && node.children && (
          <div>
            {node.children.map(child => renderNode(child))}
          </div>
        )}
      </div>
    );
  };

  const tree = buildTree();

  return (
    <div style={{ padding: '8px 0' }}>
      {tree.map(node => renderNode(node))}
    </div>
  );
};

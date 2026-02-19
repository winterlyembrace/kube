import { create } from 'zustand';
import * as api from '../api';

export const useEditorStore = create((set, get) => ({
  // Initial state
  graph: null,
  selectedNodeId: null,
  selectedFile: null,
  isAuthenticated: false,
  user: null,
  repositories: [],
  selectedRepo: null,
  selectedBranch: null,
  repoPath: '',
  validationErrors: [],
  isLoading: false,
  error: null,
  sidebarOpen: true,
  
  loadGraph: async () => {
    set({ isLoading: true, error: null });
    try {
      const graph = await api.manifests.getGraph();
      set({ graph, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to load graph', isLoading: false });
    }
  },
  
  loadFromGitHub: async (repo, branch, path) => {
    set({ isLoading: true, error: null });
    try {
      const { graph } = await api.manifests.load(repo, branch, path || '.');
      set({ 
        graph, 
        selectedRepo: repo, 
        selectedBranch: branch, 
        repoPath: path,
        isLoading: false 
      });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to load manifests', isLoading: false });
    }
  },
  
  selectNode: (nodeId) => {
    set({ selectedNodeId: nodeId });
  },
  
  selectFile: (filePath) => {
    set({ selectedFile: filePath });
  },
  
  updateNode: async (nodeId, updates) => {
    try {
      const { graph, errors } = await api.nodes.update(nodeId, updates);
      set({ graph, validationErrors: errors });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to update node' });
    }
  },
  
  deleteNode: async (nodeId) => {
    try {
      const { errors } = await api.nodes.delete(nodeId);
      const graph = get().graph;
      if (graph) {
        graph.nodes = graph.nodes.filter(n => n.id !== nodeId);
        graph.edges = graph.edges.filter(e => e.from !== nodeId && e.to !== nodeId);
        set({ graph, validationErrors: errors, selectedNodeId: null });
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to delete node' });
    }
  },
  
  updateNodePosition: (nodeId, x, y) => {
    const { graph } = get();
    if (!graph) return;
    
    const node = graph.nodes.find(n => n.id === nodeId);
    if (node) {
      node.visual.x = x;
      node.visual.y = y;
      set({ graph });
    }
  },
  
  authenticate: () => {
    window.location.href = '/api/auth/github/url';
  },
  
  checkAuth: async () => {
    try {
      const { authenticated, user } = await api.auth.getStatus();
      set({ isAuthenticated: authenticated, user: user || null });
    } catch {
      set({ isAuthenticated: false, user: null });
    }
  },
  
  logout: async () => {
    await api.auth.logout();
    set({ isAuthenticated: false, user: null, repositories: [], selectedRepo: null, selectedBranch: null });
  },
  
  loadRepositories: async () => {
    try {
      const { repositories } = await api.repos.list();
      set({ repositories });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to load repositories' });
    }
  },
  
  setRepoPath: (path) => {
    set({ repoPath: path });
  },
  
  validate: async () => {
    try {
      const { errors } = await api.validation.validateCurrent();
      set({ validationErrors: errors });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Validation failed' });
    }
  },
  
  applyChanges: async (commitMessage, createPR, prBranch) => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.apply.apply(commitMessage, createPR, prBranch);
      await get().loadGraph();
      set({ isLoading: false });
      return result;
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to apply changes', isLoading: false });
      throw err;
    }
  },
  
  toggleSidebar: () => {
    set({ sidebarOpen: !get().sidebarOpen });
  },
  
  getNodesForFile: (filePath) => {
    const { graph } = get();
    if (!graph) return [];
    return graph.nodes.filter(n => n.filePath === filePath);
  },
  
  getDirtyFiles: () => {
    const { graph } = get();
    if (!graph) return [];
    return Object.values(graph.files).filter(f => f.dirty);
  },
}));

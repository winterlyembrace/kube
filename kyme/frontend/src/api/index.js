// API client for backend communication

const API_BASE = '/api';

export async function fetchApi(endpoint, options) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || response.statusText);
  }

  return response.json();
}

// Auth endpoints
export const auth = {
  getOAuthUrl: () => fetchApi('/auth/github/url'),
  callback: (code, redirectUri) =>
    fetchApi('/auth/github/callback', {
      method: 'POST',
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    }),
  getStatus: () => fetchApi('/auth/status'),
  logout: () => fetchApi('/auth/logout', { method: 'POST' }),
};

// Repository endpoints
export const repos = {
  list: () => fetchApi('/repos'),
  getBranches: (repo) => fetchApi(`/repos/${encodeURIComponent(repo)}/branches`),
  getContents: (repo, path, branch) =>
    fetchApi(`/repos/${encodeURIComponent(repo)}/contents?path=${encodeURIComponent(path)}&branch=${encodeURIComponent(branch)}`),
};

// Manifest endpoints
export const manifests = {
  load: (repo, branch, path) =>
    fetchApi('/manifests/load', {
      method: 'POST',
      body: JSON.stringify({ repo, branch, path }),
    }),
  getGraph: () => fetchApi('/graph'),
};

// File endpoints
export const files = {
  list: () => fetchApi('/files'),
  get: (path) => fetchApi(`/files/${encodeURIComponent(path)}`),
};

// Node endpoints
export const nodes = {
  update: (nodeId, updates) =>
    fetchApi('/nodes/update', {
      method: 'POST',
      body: JSON.stringify({ nodeId, updates }),
    }),
  create: (node) =>
    fetchApi('/nodes/create', {
      method: 'POST',
      body: JSON.stringify(node),
    }),
  delete: (nodeId) =>
    fetchApi(`/nodes/${encodeURIComponent(nodeId)}`, {
      method: 'DELETE',
    }),
};

// Validation endpoints
export const validation = {
  validate: (graph) =>
    fetchApi('/validate', {
      method: 'POST',
      body: JSON.stringify({ graph }),
    }),
  validateCurrent: () => fetchApi('/validate'),
};

// Apply changes
export const apply = {
  apply: (commitMessage, createPR, prBranch) =>
    fetchApi('/apply', {
      method: 'POST',
      body: JSON.stringify({ commitMessage, createPR, prBranch }),
    }),
};

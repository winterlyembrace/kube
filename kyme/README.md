# K8s Manifest Visualizer & Editor

Production-grade visual editor for Kubernetes manifests with GitHub integration.

## Features

- 🎨 **Visual Graph Editor** - Interactive Konva-based canvas for K8s resources
- 🔗 **GitHub Integration** - OAuth login, repository browser, PR creation
- ✏️ **Object Editor** - Visual property editing for Deployments, Services, etc.
- ✅ **Validation** - Real-time validation with error highlighting
- 📁 **Multi-file Support** - Edit multiple YAML files simultaneously
- 🔒 **Git Safety** - Create branches and PRs instead of direct commits
- ✨ **Particle Animations** - Beautiful connection visualizations

## Tech Stack

**Frontend:**
- React 19 + Vite
- React Konva (canvas rendering)
- Zustand (state management)
- TypeScript types

**Backend:**
- FastAPI (Python)
- PyYAML
- GitHub REST API
- OAuth 2.0

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure GitHub OAuth
cp .env.example .env
# Edit .env with your GitHub OAuth credentials
```

### 2. GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/api/auth/github/callback`
4. Copy Client ID and Client Secret to `.env`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxy to backend)
npm run dev
```

### 4. Configure Vite Proxy

Create `frontend/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 5. Run

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

## Usage

1. **Connect GitHub** - Click "Connect GitHub" and authorize
2. **Select Repository** - Choose repo and branch with K8s manifests
3. **View Graph** - See visual representation of your resources
4. **Edit Objects** - Click any node to edit properties
5. **Apply Changes** - Click "Apply Changes" to commit or create PR

## API Endpoints

### Auth
- `GET /api/auth/github/url` - Get OAuth URL
- `POST /api/auth/github/callback` - OAuth callback
- `GET /api/auth/status` - Check auth status
- `POST /api/auth/logout` - Logout

### Repositories
- `GET /api/repos` - List repositories
- `GET /api/repos/{repo}/branches` - List branches
- `GET /api/repos/{repo}/contents` - List directory

### Manifests
- `POST /api/manifests/load` - Load manifests from repo
- `GET /api/graph` - Get current graph

### Nodes
- `POST /api/nodes/update` - Update node
- `POST /api/nodes/create` - Create node
- `DELETE /api/nodes/{id}` - Delete node

### Validation
- `GET /api/validate` - Validate current graph
- `POST /api/validate` - Validate specific graph

### Apply
- `POST /api/apply` - Apply changes (commit or PR)

## Graph Model Schema

```typescript
interface GraphModel {
  nodes: GraphNode[];
  edges: GraphEdge[];
  files: Record<string, FileInfo>;
}

interface GraphNode {
  id: string;
  kind: string;  // Deployment, Service, etc.
  name: string;
  namespace: string;
  filePath: string;
  labels: Record<string, string>;
  spec: Record<string, any>;
  visual: { x, y, width, height, icon };
  // Kind-specific fields
  replicas?: number;
  containers?: Container[];
  ports?: Port[];
  selector?: Record<string, string>;
  serviceType?: string;
}

interface GraphEdge {
  from: string;
  to: string;
  relationType: 'selector' | 'service-target' | 'ingress-backend';
}
```

## Environment Variables

### Backend (.env)
```
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
HOST=0.0.0.0
PORT=8000
```

## License

MIT

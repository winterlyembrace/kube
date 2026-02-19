#!/usr/bin/env python3
"""
K8s YAML Visualizer & Editor API

Production-grade API for Kubernetes manifests visualization and editing.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.models.graph_model import GraphModel, GraphNode, GraphEdge, FileInfo
from app.converters.yaml_converter import YamlGraphConverter
from app.github.github_client import GitHubClient, GitHubSession, github_session
from app.validation.validator import ManifestValidator, ValidationError

load_dotenv()

app = FastAPI(title="K8s YAML Visualizer & Editor API", version="2.0.0")

# CORS - allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Global state
graph_store: Dict[str, GraphModel] = {}
validator = ManifestValidator()
converter = YamlGraphConverter()


# ============== Pydantic Models ==============

class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


class RepoSelectionRequest(BaseModel):
    repo: str
    branch: str
    path: str = ""


class FileUpdateRequest(BaseModel):
    filePath: str
    content: str
    sha: str


class ApplyChangesRequest(BaseModel):
    commitMessage: str
    createPR: bool = True
    prBranch: str = ""


class NodeUpdateRequest(BaseModel):
    nodeId: str
    updates: Dict[str, Any]


class ValidateRequest(BaseModel):
    graph: Dict[str, Any]


# ============== Helper Functions ==============

def get_current_graph() -> GraphModel:
    """Get current graph from store"""
    session_key = "default"
    if session_key not in graph_store:
        graph_store[session_key] = GraphModel()
    return graph_store[session_key]


def save_graph(model: GraphModel):
    """Save graph to store"""
    graph_store["default"] = model


# ============== GitHub OAuth Endpoints ==============

@app.get("/auth/github/url")
def get_github_oauth_url(request: Request):
    """Get GitHub OAuth URL for login"""
    redirect_uri = str(request.base_url) + "api/auth/github/callback"
    client = GitHubClient()
    url = client.get_oauth_url(redirect_uri)
    return {"oauthUrl": url}


@app.post("/auth/github/callback")
def github_oauth_callback(req: OAuthCallbackRequest):
    """Handle GitHub OAuth callback"""
    try:
        client = GitHubClient()
        token = client.exchange_code_for_token(req.code, req.redirect_uri)
        
        # Store token in session
        github_session.connect(token)
        
        user = github_session.client.get_current_user()
        return {
            "success": True,
            "user": {
                "login": user.get("login"),
                "name": user.get("name"),
                "avatar": user.get("avatar_url")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/status")
def auth_status():
    """Check authentication status"""
    if github_session.token and github_session.user:
        return {
            "authenticated": True,
            "user": github_session.user
        }
    return {"authenticated": False}


@app.post("/auth/logout")
def logout():
    """Logout from GitHub"""
    github_session.token = None
    github_session.user = None
    github_session.client = None
    return {"success": True}


# ============== Repository Endpoints ==============

@app.get("/repos")
def list_repos():
    """List user repositories"""
    if not github_session.client:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        repos = github_session.client.list_repositories()
        return {
            "repositories": [
                {
                    "fullName": r.full_name,
                    "name": r.name,
                    "owner": r.owner,
                    "defaultBranch": r.default_branch,
                    "private": r.private
                }
                for r in repos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/repos/{repo_name}/branches")
def list_branches(repo_name: str):
    """List repository branches"""
    if not github_session.client:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        branches = github_session.client.list_branches(repo_name)
        return {"branches": branches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/repos/{repo_name}/contents")
def list_contents(repo_name: str, path: str = "", branch: str = "main"):
    """List directory contents"""
    if not github_session.client:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        contents = github_session.client.list_directory(repo_name, path, branch)
        return {"contents": contents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Manifest Loading Endpoints ==============

@app.post("/manifests/load")
def load_manifests(req: RepoSelectionRequest):
    """Load YAML manifests from GitHub repository"""
    if not github_session.client:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Set current repo
        github_session.set_repository(req.repo, req.branch)
        
        # Get all YAML files
        path = req.path if req.path else ""
        yaml_files = github_session.client.get_yaml_files(req.repo, path, req.branch)
        
        # Build graph model
        model = GraphModel()
        
        for file in yaml_files:
            file_model = converter.yaml_to_graph(file.decoded_content, file.path)
            model.files[file.path] = FileInfo(
                path=file.path,
                objects=file_model.files.get(file.path, FileInfo(path=file.path)).objects,
                dirty=False,
                sha=file.sha,
                content=file.decoded_content
            )
            
            for node in file_model.nodes:
                model.add_node(node)
        
        # Create edges across files
        converter._create_edges(model)
        
        save_graph(model)
        
        return {
            "success": True,
            "graph": model.to_dict(),
            "fileCount": len(yaml_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph")
def get_graph():
    """Get current graph"""
    model = get_current_graph()
    return model.to_dict()


# ============== File Operations ==============

@app.get("/files")
def list_files():
    """List all loaded files"""
    model = get_current_graph()
    return {
        "files": [
            {
                "path": info.path,
                "objects": info.objects,
                "dirty": info.dirty
            }
            for info in model.files.values()
        ]
    }


@app.get("/files/{file_path:path}")
def get_file(file_path: str):
    """Get file content"""
    model = get_current_graph()
    file_info = model.files.get(file_path)
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "path": file_info.path,
        "content": file_info.content,
        "sha": file_info.sha,
        "dirty": file_info.dirty
    }


# ============== Node Operations ==============

@app.post("/nodes/update")
def update_node(req: NodeUpdateRequest):
    """Update a node"""
    model = get_current_graph()
    
    success = model.update_node(req.nodeId, req.updates)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    
    save_graph(model)
    
    # Re-validate
    errors = validator.validate_graph(model)
    
    return {
        "success": True,
        "graph": model.to_dict(),
        "errors": [e.to_dict() for e in errors]
    }


@app.post("/nodes/create")
def create_node(req: Dict[str, Any]):
    """Create a new node"""
    model = get_current_graph()
    
    node = GraphNode.from_dict(req)
    model.add_node(node)
    save_graph(model)
    
    errors = validator.validate_graph(model)
    
    return {
        "success": True,
        "node": node.to_dict(),
        "errors": [e.to_dict() for e in errors]
    }


@app.delete("/nodes/{node_id}")
def delete_node(node_id: str):
    """Delete a node"""
    model = get_current_graph()
    model.remove_node(node_id)
    save_graph(model)
    
    errors = validator.validate_graph(model)
    
    return {
        "success": True,
        "errors": [e.to_dict() for e in errors]
    }


# ============== Validation ==============

@app.post("/validate")
def validate(req: ValidateRequest):
    """Validate graph"""
    model = GraphModel.from_dict(req.graph)
    errors = validator.validate_graph(model)
    
    return {
        "errors": [e.to_dict() for e in errors],
        "valid": not validator.has_errors()
    }


@app.get("/validate")
def validate_current():
    """Validate current graph"""
    model = get_current_graph()
    errors = validator.validate_graph(model)
    
    return {
        "errors": [e.to_dict() for e in errors],
        "valid": not validator.has_errors()
    }


# ============== Apply Changes ==============

@app.post("/apply")
def apply_changes(req: ApplyChangesRequest):
    """Apply changes to GitHub"""
    if not github_session.client:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    model = get_current_graph()
    dirty_files = model.get_dirty_files()
    
    if not dirty_files:
        return {"success": True, "message": "No changes to apply"}
    
    try:
        repo = github_session.current_repo
        branch = github_session.current_branch
        
        if not repo or not branch:
            raise HTTPException(status_code=400, detail="Repository not selected")
        
        # Create PR branch if requested
        target_branch = branch
        if req.createPR:
            pr_branch = req.prBranch or f"k8s-editor/{branch}-{os.urandom(4).hex()}"
            github_session.client.create_branch(repo, pr_branch, branch)
            target_branch = pr_branch
        
        # Update each dirty file
        updated_files = []
        for file_path in dirty_files:
            file_info = model.files[file_path]
            
            # Get current SHA
            try:
                current_file = github_session.client.get_file_content(repo, file_path, branch)
                sha = current_file.sha
            except Exception:
                sha = file_info.sha or ""
            
            # Generate new content
            content = converter.graph_to_yaml(model, file_path)
            
            # Update file
            github_session.client.update_file(
                repo=repo,
                path=file_path,
                content=content,
                message=f"{req.commitMessage}\n\nUpdated: {file_path}",
                sha=sha,
                branch=target_branch
            )
            updated_files.append(file_path)
            
            # Mark as clean
            file_info.dirty = False
        
        # Create PR if requested
        pr_url = None
        if req.createPR:
            pr = github_session.client.create_pull_request(
                repo_full_name=repo,
                title=req.commitMessage,
                body=f"Kubernetes manifest updates\n\nModified files:\n" + 
                     "\n".join(f"- {f}" for f in updated_files),
                head=target_branch,
                base=branch
            )
            pr_url = pr.get("html_url")
        
        save_graph(model)
        
        return {
            "success": True,
            "updatedFiles": updated_files,
            "prUrl": pr_url,
            "prBranch": target_branch if req.createPR else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Health Check ==============

@app.get("/")
def root():
    return {"status": "ok", "service": "k8s-yaml-editor", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}

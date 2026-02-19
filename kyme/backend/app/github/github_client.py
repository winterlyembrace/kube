#!/usr/bin/env python3
"""
GitHub Integration Module

Handles OAuth, repository access, and file operations via GitHub API.
"""

import os
import base64
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GitHubRepo:
    full_name: str
    name: str
    owner: str
    default_branch: str
    private: bool


@dataclass
class GitHubFile:
    path: str
    name: str
    sha: str
    content: str
    decoded_content: str


class GitHubClient:
    """GitHub API Client for OAuth and repository operations"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def get_oauth_url(self, redirect_uri: str) -> str:
        """Generate GitHub OAuth URL"""
        client_id = os.getenv("GITHUB_CLIENT_ID", "")
        scope = "repo"
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope}"
        )
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> str:
        """Exchange OAuth code for access token"""
        client_id = os.getenv("GITHUB_CLIENT_ID", "")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        
        response = self.session.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri
            }
        )
        
        data = response.json()
        if "access_token" in data:
            self.token = data["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            return self.token
        
        raise ValueError(f"Failed to get token: {data}")
    
    def get_current_user(self) -> Dict:
        """Get current authenticated user"""
        response = self.session.get("https://api.github.com/user")
        response.raise_for_status()
        return response.json()
    
    def list_repositories(self, username: Optional[str] = None) -> List[GitHubRepo]:
        """List user or organization repositories"""
        repos = []
        
        if username:
            url = f"https://api.github.com/users/{username}/repos"
        else:
            url = "https://api.github.com/user/repos"
        
        params = {"per_page": 100, "type": "all"}
        
        while url:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, list):
                break
                
            for repo in data:
                repos.append(GitHubRepo(
                    full_name=repo["full_name"],
                    name=repo["name"],
                    owner=repo["owner"]["login"],
                    default_branch=repo["default_branch"],
                    private=repo["private"]
                ))
            
            # Pagination
            url = response.links.get("next", {}).get("url")
            params = None
        
        return repos
    
    def list_branches(self, repo_full_name: str) -> List[str]:
        """List repository branches"""
        url = f"https://api.github.com/repos/{repo_full_name}/branches"
        response = self.session.get(url)
        response.raise_for_status()
        
        return [branch["name"] for branch in response.json()]
    
    def list_directory(self, repo_full_name: str, path: str, branch: str) -> List[Dict]:
        """List directory contents"""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
        params = {"ref": branch}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not isinstance(data, list):
            data = [data]
        
        return [
            {
                "name": item["name"],
                "path": item["path"],
                "type": item["type"],
                "sha": item.get("sha")
            }
            for item in data
        ]
    
    def get_file_content(self, repo_full_name: str, path: str, branch: str) -> GitHubFile:
        """Get file content"""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
        params = {"ref": branch}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        content = data.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8") if content else ""
        
        return GitHubFile(
            path=data["path"],
            name=data["name"],
            sha=data["sha"],
            content=content,
            decoded_content=decoded
        )
    
    def get_yaml_files(self, repo_full_name: str, path: str, branch: str) -> List[GitHubFile]:
        """Recursively get all YAML files from a directory"""
        yaml_files = []
        
        try:
            contents = self.list_directory(repo_full_name, path, branch)
        except Exception:
            return yaml_files
        
        for item in contents:
            if item["type"] == "dir":
                yaml_files.extend(
                    self.get_yaml_files(repo_full_name, item["path"], branch)
                )
            elif item["name"].endswith((".yaml", ".yml")):
                try:
                    file_content = self.get_file_content(repo_full_name, item["path"], branch)
                    yaml_files.append(file_content)
                except Exception:
                    continue
        
        return yaml_files
    
    def update_file(
        self,
        repo_full_name: str,
        path: str,
        content: str,
        message: str,
        sha: str,
        branch: str
    ) -> Dict:
        """Update or create a file"""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
        
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": message,
            "content": encoded_content,
            "sha": sha,
            "branch": branch
        }
        
        response = self.session.put(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def create_branch(
        self,
        repo_full_name: str,
        branch_name: str,
        base_branch: str
    ) -> Dict:
        """Create a new branch from base branch"""
        url = f"https://api.github.com/repos/{repo_full_name}/git/refs"
        
        # Get SHA of base branch
        base_url = f"https://api.github.com/repos/{repo_full_name}/git/refs/heads/{base_branch}"
        base_response = self.session.get(base_url)
        base_response.raise_for_status()
        base_sha = base_response.json()["object"]["sha"]
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        head: str,
        base: str
    ) -> Dict:
        """Create a pull request"""
        url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_file_sha(self, repo_full_name: str, path: str, branch: str) -> str:
        """Get file SHA for update"""
        try:
            file_info = self.get_file_content(repo_full_name, path, branch)
            return file_info.sha
        except Exception:
            return ""


class GitHubSession:
    """Manages GitHub session state"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.current_repo: Optional[str] = None
        self.current_branch: Optional[str] = None
        self.client: Optional[GitHubClient] = None
    
    def connect(self, token: str):
        """Connect with token"""
        self.token = token
        self.client = GitHubClient(token)
        self.user = self.client.get_current_user()
    
    def set_repository(self, repo_full_name: str, branch: str):
        """Set current repository and branch"""
        self.current_repo = repo_full_name
        self.current_branch = branch


# Global session instance
github_session = GitHubSession()

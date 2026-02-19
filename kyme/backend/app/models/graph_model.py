#!/usr/bin/env python3
"""
Unified JSON Graph Model for Kubernetes Resources

Schema:
{
  "nodes": [
    {
      "id": "unique-id",
      "kind": "Deployment|Service|Ingress|ConfigMap|Secret",
      "name": "resource-name",
      "namespace": "default",
      "filePath": "path/to/file.yaml",
      "labels": {...},
      "spec": {...},
      "visual": {
        "x": 0,
        "y": 0,
        "width": 80,
        "height": 80,
        "icon": "deployment"
      }
    }
  ],
  "edges": [
    {
      "from": "node-id",
      "to": "node-id",
      "relationType": "selector|service-target|volume-mount|config-ref"
    }
  ],
  "files": {
    "path/to/file.yaml": {
      "path": "path/to/file.yaml",
      "objects": ["node-id-1", "node-id-2"],
      "dirty": false,
      "sha": "abc123...",
      "content": "raw yaml content"
    }
  }
}
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class RelationType(str, Enum):
    SELECTOR = "selector"
    SERVICE_TARGET = "service-target"
    VOLUME_MOUNT = "volume-mount"
    CONFIG_REF = "config-ref"
    SECRET_REF = "secret-ref"
    INGRESS_BACKEND = "ingress-backend"


@dataclass
class VisualProps:
    x: float = 0
    y: float = 0
    width: float = 80
    height: float = 80
    icon: str = "default"


@dataclass
class GraphNode:
    id: str
    kind: str
    name: str
    namespace: str = "default"
    filePath: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    spec: Dict[str, Any] = field(default_factory=dict)
    visual: VisualProps = field(default_factory=VisualProps)
    
    # Additional K8s-specific fields
    annotations: Dict[str, str] = field(default_factory=dict)
    replicas: int = 1
    containers: List[Dict[str, Any]] = field(default_factory=list)
    ports: List[Dict[str, Any]] = field(default_factory=list)
    env: List[Dict[str, Any]] = field(default_factory=list)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    volumeMounts: List[Dict[str, Any]] = field(default_factory=dict)
    selector: Dict[str, str] = field(default_factory=dict)
    serviceType: str = "ClusterIP"
    data: Dict[str, str] = field(default_factory=dict)  # For ConfigMap/Secret
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "filePath": self.filePath,
            "labels": self.labels,
            "spec": self.spec,
            "visual": {
                "x": self.visual.x,
                "y": self.visual.y,
                "width": self.visual.width,
                "height": self.visual.height,
                "icon": self.visual.icon
            },
            "annotations": self.annotations,
            "replicas": self.replicas,
            "containers": self.containers,
            "ports": self.ports,
            "env": self.env,
            "volumes": self.volumes,
            "volumeMounts": self.volumeMounts,
            "selector": self.selector,
            "serviceType": self.serviceType,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GraphNode":
        visual = VisualProps(**data.get("visual", {}))
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            kind=data.get("kind", "Unknown"),
            name=data.get("name", ""),
            namespace=data.get("namespace", "default"),
            filePath=data.get("filePath", ""),
            labels=data.get("labels", {}),
            spec=data.get("spec", {}),
            visual=visual,
            annotations=data.get("annotations", {}),
            replicas=data.get("replicas", 1),
            containers=data.get("containers", []),
            ports=data.get("ports", []),
            env=data.get("env", []),
            volumes=data.get("volumes", []),
            volumeMounts=data.get("volumeMounts", {}),
            selector=data.get("selector", {}),
            serviceType=data.get("serviceType", "ClusterIP"),
            data=data.get("data", {})
        )


@dataclass
class GraphEdge:
    from_node: str
    to_node: str
    relationType: str
    
    def to_dict(self) -> Dict:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "relationType": self.relationType
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GraphEdge":
        return cls(
            from_node=data.get("from", ""),
            to_node=data.get("to", ""),
            relationType=data.get("relationType", "selector")
        )


@dataclass
class FileInfo:
    path: str
    objects: List[str] = field(default_factory=list)
    dirty: bool = False
    sha: Optional[str] = None
    content: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "objects": self.objects,
            "dirty": self.dirty,
            "sha": self.sha,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FileInfo":
        return cls(
            path=data.get("path", ""),
            objects=data.get("objects", []),
            dirty=data.get("dirty", False),
            sha=data.get("sha"),
            content=data.get("content", "")
        )


@dataclass
class GraphModel:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    files: Dict[str, FileInfo] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "files": {k: v.to_dict() for k, v in self.files.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GraphModel":
        nodes = [GraphNode.from_dict(n) for n in data.get("nodes", [])]
        edges = [GraphEdge.from_dict(e) for e in data.get("edges", [])]
        files = {k: FileInfo.from_dict(v) for k, v in data.get("files", {}).items()}
        return cls(nodes=nodes, edges=edges, files=files)
    
    def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_nodes_by_file(self, file_path: str) -> List[GraphNode]:
        return [n for n in self.nodes if n.filePath == file_path]
    
    def get_dirty_files(self) -> List[str]:
        return [path for path, info in self.files.items() if info.dirty]
    
    def add_node(self, node: GraphNode):
        self.nodes.append(node)
        if node.filePath and node.filePath not in self.files:
            self.files[node.filePath] = FileInfo(path=node.filePath)
        if node.filePath:
            if node.id not in self.files[node.filePath].objects:
                self.files[node.filePath].objects.append(node.id)
            self.files[node.filePath].dirty = True
    
    def remove_node(self, node_id: str):
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.from_node != node_id and e.to_node != node_id]
        for file_info in self.files.values():
            if node_id in file_info.objects:
                file_info.objects.remove(node_id)
                file_info.dirty = True
    
    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
    
    def update_node(self, node_id: str, updates: Dict) -> bool:
        for node in self.nodes:
            if node.id == node_id:
                for key, value in updates.items():
                    if hasattr(node, key):
                        setattr(node, key, value)
                if node.filePath and node.filePath in self.files:
                    self.files[node.filePath].dirty = True
                return True
        return False

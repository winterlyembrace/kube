#!/usr/bin/env python3
"""
Kubernetes Manifest Validation System

Implements both frontend and backend validation for K8s resources.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    node_id: str
    field: str
    message: str
    severity: ValidationSeverity
    file_path: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "nodeId": self.node_id,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "filePath": self.file_path
        }


class ManifestValidator:
    """Validates Kubernetes manifests"""
    
    REQUIRED_FIELDS = {
        "Deployment": ["metadata.name", "spec.selector.matchLabels", "spec.template"],
        "Service": ["metadata.name", "spec.selector", "spec.ports"],
        "Ingress": ["metadata.name", "spec.rules"],
        "ConfigMap": ["metadata.name"],
        "Secret": ["metadata.name"],
        "Pod": ["metadata.name", "spec.containers"],
    }
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate_graph(self, graph: "GraphModel") -> List[ValidationError]:
        """Validate entire graph model"""
        self.errors = []
        
        # Check for duplicate names
        self._check_duplicate_names(graph)
        
        # Validate each node
        for node in graph.nodes:
            self._validate_node(node)
        
        # Check selector consistency
        self._check_selector_consistency(graph)
        
        # Check service selectors match workloads
        self._check_service_selectors(graph)
        
        # Validate ports
        self._validate_ports(graph)
        
        # Validate image names
        self._validate_image_names(graph)
        
        return self.errors
    
    def _check_duplicate_names(self, graph: "GraphModel"):
        """Check for duplicate resource names"""
        name_map: Dict[str, List[str]] = {}
        
        for node in graph.nodes:
            key = f"{node.kind}/{node.namespace}/{node.name}"
            if key not in name_map:
                name_map[key] = []
            name_map[key].append(node.id)
        
        for key, node_ids in name_map.items():
            if len(node_ids) > 1:
                for node_id in node_ids[1:]:
                    node = graph.get_node_by_id(node_id)
                    if node:
                        self.errors.append(ValidationError(
                            node_id=node_id,
                            field="metadata.name",
                            message=f"Duplicate {node.kind} name: {node.name}",
                            severity=ValidationSeverity.ERROR,
                            file_path=node.filePath
                        ))
    
    def _validate_node(self, node: "GraphNode"):
        """Validate individual node"""
        required = self.REQUIRED_FIELDS.get(node.kind, [])
        
        for field_path in required:
            if not self._has_field(node, field_path):
                self.errors.append(ValidationError(
                    node_id=node.id,
                    field=field_path,
                    message=f"Missing required field: {field_path}",
                    severity=ValidationSeverity.ERROR,
                    file_path=node.filePath
                ))
    
    def _has_field(self, node: "GraphNode", field_path: str) -> bool:
        """Check if node has a field"""
        parts = field_path.split(".")
        obj = node
        
        for part in parts:
            if isinstance(obj, dict):
                if part not in obj:
                    return False
                obj = obj[part]
            elif hasattr(obj, part):
                obj = getattr(obj, part)
                if obj is None:
                    return False
            else:
                return False
        
        return bool(obj) if not isinstance(obj, bool) else True
    
    def _check_selector_consistency(self, graph: "GraphModel"):
        """Check selector matches labels for Deployments"""
        for node in graph.nodes:
            if node.kind == "Deployment":
                selector = node.selector
                labels = node.labels
                
                if selector and labels:
                    for key, value in selector.items():
                        if labels.get(key) != value:
                            self.errors.append(ValidationError(
                                node_id=node.id,
                                field="spec.selector.matchLabels",
                                message=f"Selector '{key}={value}' does not match template labels",
                                severity=ValidationSeverity.ERROR,
                                file_path=node.filePath
                            ))
    
    def _check_service_selectors(self, graph: "GraphModel"):
        """Check that Service selectors match at least one workload"""
        services = [n for n in graph.nodes if n.kind == "Service"]
        workloads = [n for n in graph.nodes if n.kind in ["Deployment", "Pod", "StatefulSet"]]
        
        for service in services:
            selector = service.selector
            if not selector:
                continue
            
            matched = False
            for workload in workloads:
                if self._selector_matches(selector, workload.labels):
                    matched = True
                    break
            
            if not matched and selector:
                self.errors.append(ValidationError(
                    node_id=service.id,
                    field="spec.selector",
                    message=f"Service selector does not match any workload",
                    severity=ValidationSeverity.WARNING,
                    file_path=service.filePath
                ))
    
    def _selector_matches(self, selector: Dict[str, str], labels: Dict[str, str]) -> bool:
        """Check if selector matches labels"""
        for key, value in selector.items():
            if labels.get(key) != value:
                return False
        return True
    
    def _validate_ports(self, graph: "GraphModel"):
        """Validate port numbers"""
        for node in graph.nodes:
            if node.kind == "Service":
                for port in node.ports:
                    port_num = port.get("port", 0)
                    if not isinstance(port_num, int) or port_num < 1 or port_num > 65535:
                        self.errors.append(ValidationError(
                            node_id=node.id,
                            field="spec.ports",
                            message=f"Invalid port number: {port_num}",
                            severity=ValidationSeverity.ERROR,
                            file_path=node.filePath
                        ))
                    
                    target_port = port.get("targetPort", port_num)
                    if isinstance(target_port, int) and (target_port < 1 or target_port > 65535):
                        self.errors.append(ValidationError(
                            node_id=node.id,
                            field="spec.ports.targetPort",
                            message=f"Invalid targetPort: {target_port}",
                            severity=ValidationSeverity.ERROR,
                            file_path=node.filePath
                        ))
    
    def _validate_image_names(self, graph: "GraphModel"):
        """Validate container image names"""
        for node in graph.nodes:
            if node.kind == "Deployment":
                for container in node.containers:
                    image = container.get("image", "")
                    if not image:
                        self.errors.append(ValidationError(
                            node_id=node.id,
                            field="spec.template.spec.containers.image",
                            message="Container image is required",
                            severity=ValidationSeverity.ERROR,
                            file_path=node.filePath
                        ))
                    elif not self._is_valid_image_name(image):
                        self.errors.append(ValidationError(
                            node_id=node.id,
                            field="spec.template.spec.containers.image",
                            message=f"Invalid image name format: {image}",
                            severity=ValidationSeverity.WARNING,
                            file_path=node.filePath
                        ))
    
    def _is_valid_image_name(self, image: str) -> bool:
        """Basic image name validation"""
        if not image:
            return False
        # Basic pattern: [registry/][repo/]name[:tag][@digest]
        # This is simplified validation
        invalid_chars = set(' \t\n\r')
        return not any(c in invalid_chars for c in image)
    
    def get_errors_for_node(self, node_id: str) -> List[ValidationError]:
        """Get all errors for a specific node"""
        return [e for e in self.errors if e.node_id == node_id]
    
    def get_errors_for_file(self, file_path: str) -> List[ValidationError]:
        """Get all errors for a specific file"""
        return [e for e in self.errors if e.file_path == file_path]
    
    def has_errors(self, node_id: Optional[str] = None) -> bool:
        """Check if there are any errors"""
        if node_id:
            return any(e.node_id == node_id and e.severity == ValidationSeverity.ERROR 
                      for e in self.errors)
        return any(e.severity == ValidationSeverity.ERROR for e in self.errors)

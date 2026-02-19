#!/usr/bin/env python3
"""
YAML to Graph Model Converter

Converts Kubernetes YAML manifests to unified graph model and back.
"""

import yaml
from typing import Dict, List, Any, Optional
from app.models.graph_model import GraphModel, GraphNode, GraphEdge, FileInfo, RelationType


class YamlGraphConverter:
    """Converts between Kubernetes YAML and GraphModel"""
    
    KIND_ICON_MAP = {
        "Deployment": "deployment",
        "Service": "service",
        "Ingress": "ingress",
        "Pod": "pod",
        "ConfigMap": "configmap",
        "Secret": "secret",
        "PersistentVolumeClaim": "pvc",
        "StatefulSet": "statefulset",
        "DaemonSet": "daemonset",
        "Job": "job",
        "CronJob": "cronjob"
    }
    
    def parse_yaml_content(self, content: str, file_path: str) -> List[Dict]:
        """Parse multi-document YAML content"""
        docs = []
        for doc in yaml.safe_load_all(content):
            if isinstance(doc, dict):
                doc['_sourceFile'] = file_path
                docs.append(doc)
        return docs
    
    def create_node_id(self, kind: str, name: str, namespace: str) -> str:
        """Create unique node ID"""
        return f"{kind.lower()}/{namespace}/{name}"
    
    def yaml_to_graph(self, content: str, file_path: str) -> GraphModel:
        """Convert YAML content to GraphModel"""
        model = GraphModel()
        docs = self.parse_yaml_content(content, file_path)
        
        # Initialize file info
        file_info = FileInfo(path=file_path, content=content)
        
        for doc in docs:
            kind = doc.get("kind", "")
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", "default")
            labels = metadata.get("labels", {})
            annotations = metadata.get("annotations", {})
            spec = doc.get("spec", {})
            
            if not name or not kind:
                continue
            
            node_id = self.create_node_id(kind, name, namespace)
            icon = self.KIND_ICON_MAP.get(kind, "default")
            
            node = GraphNode(
                id=node_id,
                kind=kind,
                name=name,
                namespace=namespace,
                filePath=file_path,
                labels=labels,
                annotations=annotations,
                spec=spec,
                visual={"icon": icon}
            )
            
            # Extract kind-specific properties
            if kind == "Deployment":
                node.replicas = spec.get("replicas", 1)
                node.selector = spec.get("selector", {}).get("matchLabels", {})
                
                template = spec.get("template", {})
                template_spec = template.get("spec", {})
                
                # Extract containers
                containers = template_spec.get("containers", [])
                node.containers = []
                for c in containers:
                    node.containers.append({
                        "name": c.get("name", ""),
                        "image": c.get("image", ""),
                        "ports": c.get("ports", []),
                        "env": c.get("env", []),
                        "volumeMounts": c.get("volumeMounts", [])
                    })
                
                # Extract volumes
                node.volumes = template_spec.get("volumes", [])
                
                # Extract pod labels
                template_labels = template.get("metadata", {}).get("labels", {})
                node.labels = {**labels, **template_labels}
                
            elif kind == "Service":
                node.serviceType = spec.get("type", "ClusterIP")
                node.selector = spec.get("selector", {})
                
                # Extract ports
                ports = spec.get("ports", [])
                node.ports = []
                for p in ports:
                    node.ports.append({
                        "name": p.get("name", ""),
                        "port": p.get("port", 80),
                        "targetPort": p.get("targetPort", p.get("port", 80)),
                        "protocol": p.get("protocol", "TCP")
                    })
                    
            elif kind == "Ingress":
                # Store rules for edge creation
                node.spec = spec
                
            elif kind == "ConfigMap":
                node.data = doc.get("data", {})
                
            elif kind == "Secret":
                node.data = doc.get("data", {})
            
            model.add_node(node)
            file_info.objects.append(node_id)
        
        model.files[file_path] = file_info
        
        # Create edges based on relationships
        self._create_edges(model)
        
        return model
    
    def _create_edges(self, model: GraphModel):
        """Create edges between related nodes"""
        
        # Service -> Deployment/Pod (via selector)
        for service_node in [n for n in model.nodes if n.kind == "Service"]:
            for workload_node in [n for n in model.nodes if n.kind in ["Deployment", "Pod", "StatefulSet"]]:
                if self._selector_matches(service_node.selector, workload_node.labels):
                    model.add_edge(GraphEdge(
                        from_node=service_node.id,
                        to_node=workload_node.id,
                        relationType=RelationType.SELECTOR.value
                    ))
        
        # Ingress -> Service (via backend)
        for ingress_node in [n for n in model.nodes if n.kind == "Ingress"]:
            rules = ingress_node.spec.get("rules", [])
            for rule in rules:
                http = rule.get("http", {})
                paths = http.get("paths", [])
                for path in paths:
                    backend = path.get("backend", {})
                    service = backend.get("service", {})
                    service_name = service.get("name", "")
                    
                    # Find matching service
                    for service_node in [n for n in model.nodes if n.kind == "Service"]:
                        if service_node.name == service_name:
                            model.add_edge(GraphEdge(
                                from_node=ingress_node.id,
                                to_node=service_node.id,
                                relationType=RelationType.INGRESS_BACKEND.value
                            ))
        
        # Deployment -> ConfigMap/Secret (via envFrom, volumes)
        for deployment_node in [n for n in model.nodes if n.kind == "Deployment"]:
            for container in deployment_node.containers:
                # Check envFrom
                env_from = container.get("env", [])
                for env in env_from:
                    config_map_ref = env.get("valueFrom", {}).get("configMapKeyRef", {})
                    if config_map_ref.get("name"):
                        for cm_node in [n for n in model.nodes if n.kind == "ConfigMap"]:
                            if cm_node.name == config_map_ref["name"]:
                                model.add_edge(GraphEdge(
                                    from_node=deployment_node.id,
                                    to_node=cm_node.id,
                                    relationType=RelationType.CONFIG_REF.value
                                ))
                    
                    secret_ref = env.get("valueFrom", {}).get("secretKeyRef", {})
                    if secret_ref.get("name"):
                        for secret_node in [n for n in model.nodes if n.kind == "Secret"]:
                            if secret_node.name == secret_ref["name"]:
                                model.add_edge(GraphEdge(
                                    from_node=deployment_node.id,
                                    to_node=secret_node.id,
                                    relationType=RelationType.SECRET_REF.value
                                ))
                
                # Check volumeMounts
                for vm in container.get("volumeMounts", []):
                    for volume in deployment_node.volumes:
                        if volume.get("name") == vm.get("name"):
                            config_map = volume.get("configMap", {})
                            if config_map.get("name"):
                                for cm_node in [n for n in model.nodes if n.kind == "ConfigMap"]:
                                    if cm_node.name == config_map["name"]:
                                        model.add_edge(GraphEdge(
                                            from_node=deployment_node.id,
                                            to_node=cm_node.id,
                                            relationType=RelationType.CONFIG_REF.value
                                        ))
                            
                            secret = volume.get("secret", {})
                            if secret.get("secretName"):
                                for secret_node in [n for n in model.nodes if n.kind == "Secret"]:
                                    if secret_node.name == secret["secretName"]:
                                        model.add_edge(GraphEdge(
                                            from_node=deployment_node.id,
                                            to_node=secret_node.id,
                                            relationType=RelationType.SECRET_REF.value
                                        ))
    
    def _selector_matches(self, selector: Dict[str, str], labels: Dict[str, str]) -> bool:
        """Check if selector matches labels"""
        if not selector:
            return False
        for key, value in selector.items():
            if labels.get(key) != value:
                return False
        return True
    
    def graph_to_yaml(self, model: GraphModel, file_path: str) -> str:
        """Convert GraphModel back to YAML content for a specific file"""
        file_info = model.files.get(file_path)
        if not file_info:
            return ""
        
        documents = []
        
        for node in model.nodes:
            if node.filePath != file_path:
                continue
            
            doc = self._node_to_k8s_manifest(node)
            documents.append(doc)
        
        if not documents:
            return ""
        
        return yaml.dump_all(documents, default_flow_style=False, sort_keys=False)
    
    def _node_to_k8s_manifest(self, node: GraphNode) -> Dict:
        """Convert GraphNode to Kubernetes manifest dict"""
        manifest = {
            "apiVersion": self._get_api_version(node.kind),
            "kind": node.kind,
            "metadata": {
                "name": node.name,
                "namespace": node.namespace,
            }
        }
        
        if node.labels:
            manifest["metadata"]["labels"] = node.labels
        if node.annotations:
            manifest["metadata"]["annotations"] = node.annotations
        
        spec = {}
        
        if node.kind == "Deployment":
            spec = {
                "replicas": node.replicas,
                "selector": {
                    "matchLabels": node.selector
                },
                "template": {
                    "metadata": {
                        "labels": node.labels
                    },
                    "spec": {
                        "containers": []
                    }
                }
            }
            
            if node.containers:
                for container in node.containers:
                    container_spec = {
                        "name": container.get("name", node.name),
                        "image": container.get("image", "nginx:latest"),
                    }
                    if container.get("ports"):
                        container_spec["ports"] = container["ports"]
                    if container.get("env"):
                        container_spec["env"] = container["env"]
                    if container.get("volumeMounts"):
                        container_spec["volumeMounts"] = container["volumeMounts"]
                    spec["template"]["spec"]["containers"].append(container_spec)
            
            if node.volumes:
                spec["template"]["spec"]["volumes"] = node.volumes
                
        elif node.kind == "Service":
            spec = {
                "type": node.serviceType,
                "selector": node.selector,
                "ports": node.ports if node.ports else [{"port": 80, "targetPort": 80}]
            }
            
        elif node.kind == "Ingress":
            spec = node.spec if node.spec else {
                "rules": []
            }
            
        elif node.kind in ["ConfigMap", "Secret"]:
            if node.data:
                manifest[node.kind.lower() == "configmap" and "data" or "data"] = node.data
        
        manifest["spec"] = spec
        return manifest
    
    def _get_api_version(self, kind: str) -> str:
        """Get API version for resource kind"""
        api_versions = {
            "Deployment": "apps/v1",
            "Service": "v1",
            "Ingress": "networking.k8s.io/v1",
            "Pod": "v1",
            "ConfigMap": "v1",
            "Secret": "v1",
            "PersistentVolumeClaim": "v1",
            "StatefulSet": "apps/v1",
            "DaemonSet": "apps/v1",
            "Job": "batch/v1",
            "CronJob": "batch/v1"
        }
        return api_versions.get(kind, "v1")
    
    def merge_models(self, target: GraphModel, source: GraphModel) -> GraphModel:
        """Merge source model into target model"""
        for node in source.nodes:
            existing = target.get_node_by_id(node.id)
            if existing:
                target.update_node(node.id, node.to_dict())
            else:
                target.add_node(node)
        
        for path, file_info in source.files.items():
            if path not in target.files:
                target.files[path] = file_info
            else:
                target.files[path].objects = list(set(
                    target.files[path].objects + file_info.objects
                ))
        
        return target

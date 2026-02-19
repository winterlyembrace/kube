#!/usr/bin/python3

from .classes import Service, Ingress, Pod, Deployment


def create_k8s_objects(raw_yaml_data):
    k8s_objects = []

    for doc in raw_yaml_data:
        kind = doc.get("kind")
        meta = doc.get("metadata", {})
        spec = doc.get("spec", {})
        name = meta.get("name")
        
        if not name:
            continue

        if kind == "Service":
            ports = []
            target_ports = []

            for p in spec.get("ports", []):
                if p.get("port"):
                    ports.append(p["port"])
                if p.get("targetPort"):
                    target_ports.append(p["targetPort"])

            k8s_objects.append(
                Service(name, spec.get("selector"), ports, target_ports)
            )

# Формирование свойств деплоймента:
        elif kind == "Deployment":
            match_labels = spec.get("selector", {}).get("matchLabels", {}) or {}
            match_pod_name = match_labels.get("app")
            k8s_objects.append(Deployment(name, match_pod_name))

# Формирование свойств пода:
            template = spec.get("template", {}) or {}
            pod_metadata = template.get("metadata", {})
            labels = pod_metadata.get("labels", {}) or {}
            
            replicas = (
                spec.get("replicas")
            )
            pod_name = labels.get("app")
        
            parent = name
            
            if pod_name:
                k8s_objects.append(Pod(pod_name, replicas, labels, parent))

        elif kind == "Ingress":
            backends = []

            for rule in spec.get("rules", []):
                paths = rule.get("http", {}).get("paths", [])
                for p in paths:
                    svc = p.get("backend", {}).get("service", {})
                    backends.append({
                        "service": svc.get("name"),
                        "port": svc.get("port", {}).get("number")
                    })

            k8s_objects.append(Ingress(name, backends))

    return k8s_objects 


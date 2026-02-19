#!/usr/bin/python3

from .yaml_reader import load_raw_yaml_data

class K8sResource:
    def __init__(self, kind, name):
        self.kind = kind
        self.name = name
        self.attrs = {}
        self.links = []

    def link_to(self, other, info=None):
        self.links.append({
            "to": other.name,
            "kind": other.kind,
            "info": info
        })


class Service(K8sResource):
    def __init__(self, name, selector, ports, target_ports):
        super().__init__("Service", name)
        self.selector = selector or {}
        self.ports = ports
        self.target_ports = target_ports


class Deployment(K8sResource):
    def __init__(self, name, match_pod_name):
        super().__init__("Deployment", name)
        self.match_pod_name = match_pod_name

class Ingress(K8sResource):
    def __init__(self, name, backends):
        super().__init__("Ingress", name)
        self.backends = backends

class Pod(K8sResource):
    def __init__(self, pod_name, replicas, labels, parent):
        super().__init__("Pod", pod_name)
        self.replicas = replicas
        # на самом деле это лейбы деплоймента, а не пода (пока костыль)
        self.labels = labels or {}
        self.parent = parent

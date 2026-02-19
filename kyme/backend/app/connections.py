#!/usr/bin/python3

def build_connections(k8s_objects):

    services = {r.name: r for r in k8s_objects if r.kind == "Service"}
    pods = [r for r in k8s_objects if r.kind == "Pod"]

    for svc in services.values():
        if not svc.selector:
            continue

        for pod in pods:
            if all(item in pod.labels.items() for item in svc.selector.items()):
                svc.link_to(pod, info="selector match")

    # Ingress → Service
    for r in k8s_objects:
        if r.kind != "Ingress":
            continue

        for b in r.backends:
            svc = services.get(b["service"])
            if svc:
                r.link_to(svc, info=f"port {b['port']}")


#!/usr/bin/python3

import json


def transform_to_json(k8s_objects, path):

    nodes = []
    edges = []

    for r in k8s_objects:
        nodes.append({
            "id": r.name,
            "kind": r.kind,
            "parent": r.parent
        })

        for link in r.links:
            edges.append({
                "from": r.name,
                "to": link["to"],
                "info": link["info"]
            })

    graph = {
        "nodes": nodes,
        "edges": edges
    }

    with open(path, "w") as f:
        json.dump(graph, f, indent=2)


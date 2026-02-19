#!/usr/bin/python3

from .yaml_reader import load_raw_yaml_data
from .objects_creation import create_k8s_objects
from .connections import build_connections
from .objects_to_json import transform_to_json


raw_yaml_data = load_raw_yaml_data("manifests/**/*.yaml")

k8s_objects = create_k8s_objects(raw_yaml_data)

build_connections(k8s_objects)

transform_to_json(k8s_objects, "output/graph.json")

print("граф построен → output/graph.json")


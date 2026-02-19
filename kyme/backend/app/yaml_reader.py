#!/usr/bin/python3

import glob
import yaml


def load_raw_yaml_data(path_pattern):
    raw_yaml_data = []

    for path in glob.glob(path_pattern, recursive=True):
        with open(path) as f:
            for doc in yaml.safe_load_all(f):
                if isinstance(doc, dict):
                    raw_yaml_data.append(doc)

    return raw_yaml_data


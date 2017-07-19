import yaml


def load_config(conf_file):
    with open(conf_file) as stream:
        return yaml.safe_load(stream)

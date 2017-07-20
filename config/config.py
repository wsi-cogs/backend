import yaml


def load_config(conf_path):
    """
    Load the configuration file at the file path `conf_path`

    :param conf_path:
    :return:
    """
    with open(conf_path) as stream:
        return yaml.safe_load(stream)

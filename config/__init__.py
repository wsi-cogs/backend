from collections import OrderedDict

import yaml


def load_config(conf_path):
    """
    Load the configuration file at the file path `conf_path`

    :param conf_path:
    :return:
    """
    with open(conf_path) as stream:
        # Used implementation for getting OrderedDict from https://stackoverflow.com/a/21912744/3398583
        class OrderedLoader(yaml.SafeLoader):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return OrderedDict(loader.construct_pairs(node))

        OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                      construct_mapping)
        return yaml.load(stream, OrderedLoader)

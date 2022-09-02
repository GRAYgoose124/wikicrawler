import os
import json


def init_config():
    env_root = os.getenv('WIKICRAWLER_ROOT')

    data_root = None
    if env_root is not None:
        data_root = os.path.expanduser(env_root)
    else:
        data_root = os.path.expanduser("~/.wikicrawler")

    config_file = data_root + "/config.json"

    config = None
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        config = {  'data_root': data_root,
                    'media_folder': data_root + '/images',
                    'db_file': data_root +'/databases/arbiter.db',
                    'search_precaching': False,
                    'latex': True,
                    'save_media': True  }

        with open(config_file, "w") as f:
            json.dump(config, f)

    return config

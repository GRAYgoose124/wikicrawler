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
                    'media_folder': '/images',
                    'db_file': '/arbiter.db',
                    'search_precaching': False,
                    'latex': True,
                    'save_media': False,
                    'process_media_links': False,
                    'prompt_state': None,
                    'pointer_state': None,
                    'functions_cache': None,
                    'wiki_api_token': None}

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    return config

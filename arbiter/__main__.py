import argparse
import os
import json

from core.crawler import WikiCrawler
from core.db.cacher import WikiCacher

from cli import WikiPrompt


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

def main():
    config = init_config()

    with WikiCacher(config['db_file']) as wc:
        crawler = WikiCrawler(config['data_root'], 
                                convert_latex=config['latex'], 
                                media_folder=config['media_folder'], 
                                save_media=config['save_media'], 
                            cacher=wc)

        prompt = WikiPrompt(config['data_root'], crawler, search_precaching=config['search_precaching'])

        prompt.loop()


if __name__ == '__main__':
    main()
import argparse
import os
import json

from ..core.crawler import WikiCrawler
from ..core.db.cacher import WikiCacher
from ..core.utils.config import init_config

from .cli import WikiPrompt


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
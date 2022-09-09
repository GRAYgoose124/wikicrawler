import argparse
import os
import json
import nltk
import logging

from ..core.crawler import WikiCrawler
from ..core.db.cacher import WikiCacher
from ..core.utils.config import init_config

from .cli import WikiPrompt


logging.basicConfig(format='%(name)s:%(lineno)d::%(levelname)s> %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    config = init_config()

    nltk.download('wordnet')
    nltk.download('omw-1.4')

    with WikiCacher(config['db_file']) as wc:
        crawler = WikiCrawler(config['data_root'], 
                                convert_latex=config['latex'], 
                                media_folder=config['media_folder'], 
                                save_media=config['save_media'], 
                            cacher=wc)

        prompt = WikiPrompt(config['data_root'], crawler, search_precaching=config['search_precaching'])

        logger.info("Arbiter started, enjoy your tumble.")
        prompt.loop()
        prompt.save_state()


if __name__ == '__main__':
    
    main()
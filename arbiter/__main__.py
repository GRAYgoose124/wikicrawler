import argparse
import os

from core.crawler import WikiCrawler
from core.db.cacher import WikiCacher

from cli import WikiPrompt


if __name__ == '__main__':
    with WikiCacher(os.getcwd() + '/data/databases/cli.db') as wc:
        crawler = WikiCrawler(cacher=wc)
        prompt = WikiPrompt(crawler=crawler)

        prompt.start_loop()

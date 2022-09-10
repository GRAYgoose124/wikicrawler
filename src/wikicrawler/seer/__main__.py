from wikicrawler.core.db.cacher import WikiCacher
from ..core.utils.config import init_config
from .markdown import MarkdownBuilder


def main():
    config = init_config()

    with WikiCacher(config) as wc:
        md = MarkdownBuilder(config, cacher=wc)
        md.build()


if __name__ == '__main__':

    main()
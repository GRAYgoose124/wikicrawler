import nltk
import logging

from ..core.crawler import WikiCrawler
from ..core.db.cacher import WikiCacher
from ..core.utils.config import init_config

from .prompt import WikiPrompt
from ..seer.markdown import MarkdownBuilder

logging.basicConfig(format='%(name)s:%(lineno)d::%(levelname)s> %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    config = init_config()

    nltk.download('wordnet')
    nltk.download('omw-1.4')

    with WikiCacher(config) as wc:
        crawler = WikiCrawler(config, cacher=wc)
        prompt = WikiPrompt(config, crawler, cacher=wc)

        logger.info("Arbiter started, enjoy your tumble.")
        prompt.loop()


if __name__ == '__main__':
    
    main()
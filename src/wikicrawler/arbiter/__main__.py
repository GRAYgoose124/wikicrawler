import nltk
import logging


from .app import AsyncCLI


def main():
    logging.basicConfig(format='%(name)s:%(lineno)d::%(levelname)s> %(message)s', level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.handlers.clear()
    logger.addHandler(logging.FileHandler('wikicrawler.log', mode='a+'))

    logger.info("\n\nStarting Wikicrawler Arbiter")
    
    try:
        nltk.download('wordnet')
        nltk.download('omw-1.4')
    except KeyboardInterrupt:
        pass

    try:
        app = AsyncCLI(parent_logger=logger)
        app.run()
    except KeyboardInterrupt:
        app.exit()


if __name__ == '__main__':
    main()
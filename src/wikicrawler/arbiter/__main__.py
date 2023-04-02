import nltk
import logging


from .app import AsyncCLI




def main():
    logging.basicConfig(format='%(name)s:%(lineno)d::%(levelname)s> %(message)s', level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    try:
        nltk.download('wordnet')
        nltk.download('omw-1.4')
    except KeyboardInterrupt:
        pass
    
    app = AsyncCLI()
    app.run()

if __name__ == '__main__':
    main()
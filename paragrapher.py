import nltk
from nltk.corpus import words
from nltk.sentiment import SentimentIntensityAnalyzer

import keras
from rich import print
from rich.console import Console
from rich.color import Color
from rich.highlighter import Highlighter
from random import randint

from wiki import WikiCrawler


console = Console()


filterwords = ['the', 'of', 'and', 'is', 'a', 'that', 'to', 'as']
blacklist = [',', '.', '(', ')', '``', "''", "[", "]"] + filterwords


class SentimentHighlighter(Highlighter):
    def highlight(self, text):
        for index in range(len(text)):
            text.stylize(f"color({randint(16, 255)})", index, index + 1)

def loop():
    sentiment = SentimentHighlighter()

    traversal_depth = 16
    traversal_limit = 10000
    
    urls = ['http://en.wikipedia.org/wiki/Philosophy', 'https://en.wikipedia.org/wiki/Existence', 'https://en.wikipedia.org/wiki/Cult']

    sia = SentimentIntensityAnalyzer()

    with WikiCrawler('wikipedia.db') as wc:
        pages = {}
        while len(urls) > 0:
            url = urls.pop()
            wiki = wc.retrieve(url)
            pages[wiki['title']] = wiki

        for title, page in pages.items():
            console.print(f"[bold magenta]{title}[/bold magenta]")

            body = " ".join(page['paragraphs'])
            sentences = nltk.sent_tokenize(body)
            words = list(filter(lambda x: x not in blacklist, nltk.word_tokenize(body)))
            text = nltk.Text(words)

            pages[title]['vocab'] = text.vocab()
            pages[title]['collocations'] = text.collocations() 
            print(pages[title]['collocations'])
            print(pages[title]['vocab'])

            pages[title]['sia_scores'] = [(sent, sia.polarity_scores(sent)) for sent in sentences]
            # avg_score = { 'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0 }

            for sent, score in pages[title]['sia_scores']:
                # avg_score =  { 'neg': (avg_score['neg'] + score['neg']) * 0.5, 
                #                'neu': (avg_score['neu'] + score['neu']) * 0.5, 
                #                'pos': (avg_score['pos'] + score['pos']) * 0.5, 
                #                'compound': (avg_score['compound'] + score['compound']) * 0.5}
                
                r = int(255*(score['neg']))
                g = int(255*(score['pos']))
                b = int(255*(score['neu']))
                c = int(127*(1+score['compound']))

                for word in nltk.word_tokenize(sent):
                    score = sia.polarity_scores(word)
                    x = int(0.5*(c+int(127*(1+score['compound']))))
                    console.print(word, sep=" ", end=" ", style=f"rgb({int(0.5 * (r + 255*(score['neg'])))},{int(0.5 * (g + 255*(score['pos'])))},{int(0.5 * (b + 255*(score['neu'])))}) on rgb({x},{x},{x})", highlight=False)
               
                # console.print(sent, style=f"rgb(r,g,b) on rgb({c},{c},{c})",)

            console.print()
            
if __name__ == '__main__' :
    loop()
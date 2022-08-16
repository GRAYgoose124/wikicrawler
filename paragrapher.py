#!/usr/bin/python

import time
import argparse
from random import randint

import nltk
from nltk.corpus import words, stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import BigramCollocationFinder, TrigramCollocationFinder, BigramAssocMeasures, TrigramAssocMeasures
from nltk.probability import FreqDist

from rich import print
from rich.console import Console
from rich.color import Color
from rich.highlighter import Highlighter

from input_timeout import input_with_timeout
from inputimeout import inputimeout, TimeoutOccurred

from wiki import WikiCrawler


console = Console()


fillerwords = ['at', 'their', 'been', 'which', 'on', 
                'was', 'also', 'from','we', 'can','the', 'of', 
                'and', 'is', 'a', 'that', 'to', 'as', 'in', 'are', 
                'or', 'not', 'by', 'be', 'it', "'s", 'i', 'for', 
                'with', 'an', 'has', 'have', 'some', 'were', 'but', 
                'this', 'its', 'such', 'who', 'his', 'her']
blacklist = ['!', "'", ':', '_', '\\', ',', '.', '(', ')', '{', '}', '``', "''", "[", "]"] + fillerwords


def print_sentiment(sentences):
    sia = SentimentIntensityAnalyzer()

    # avg_score = { 'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0 }
    for sent in sentences:
        score = sia.polarity_scores(sent)
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
    print()


def parse_page(page):
    # TODO: change vocab() to manual call (factoring out Text) and use TrigramCollocationFinder instead of Text.collocation_list
    body = " ".join(page['paragraphs'])
    sentences = nltk.sent_tokenize(body)
    words = nltk.word_tokenize(body)
    filtered_words = list(filter(lambda x: x.lower() not in blacklist and not x.isnumeric(), words))

    # n-grams
    filterstops = lambda w: len(w) < 3 or w in set(stopwords.words('english'))
    bcf = BigramCollocationFinder.from_words(words)
    bcf.apply_word_filter(filterstops)

    tcf = TrigramCollocationFinder.from_words(words)
    tcf.apply_word_filter(filterstops)
    tcf.apply_freq_filter(3)

    word_freq = FreqDist(filtered_words)
    bigrams = bcf.nbest(BigramAssocMeasures.likelihood_ratio, 15)
    trigrams = tcf.nbest(TrigramAssocMeasures.likelihood_ratio, 10)

    collocs = bigrams + trigrams

    return body, sentences, words, word_freq, collocs


def analyze_pages(pages):
    structs = {}

    for title, page in pages.items():
       structs[title] = analyze_page(page)

    return structs


def analyze_page(page):
    body, sentences, words, word_freq, collocs = page['stats']

    console.print(f"{'-'*80}\n[bold yellow]{page['title']} - {page['url']}[/bold yellow]")

    print(word_freq, f'\n[bold magenta]Collocations[/bold magenta]({[" ".join(entry) for entry in collocs]})\n')
    print("[bold magenta]Sentences[/bold magenta]\n\t[bold red]First 5:[/bold red]")
    print_sentiment(sentences[:5])

    tp_idx = int(.33*len(sentences))
    print("\t[bold red]30% + 10:[/bold red]")
    print_sentiment(sentences[tp_idx:tp_idx+10])

    print("\t[bold red]Last 5:[/bold red]")
    print_sentiment(sentences[-5:])


def interactive_loop():
    traversal_depth = 16
    traversal_limit = 10000
    
    urls = []
    finished_urls = []
    with open('urls.txt') as f:
        for line in f:
            # urls if you want to print on start history
            finished_urls.append(line)

    with WikiCrawler('wikipedia.db') as wc:
        pages = {}
        structs = {}

        while True:
            try:
                url = urls.pop()
                finished_urls.append(url)
                
                wiki = wc.retrieve(url)
                pages[wiki['title']] = wiki
                structs[wiki['title']] = analyze_page(wiki)
            except:
                pass

            # daemon
            while len(urls) < 1:
                # From stdin
                user_url = input_with_timeout("Enter a wiki URL: ", timeout=3)

                if user_url is not None and wc.wiki_regex.match(user_url) and user_url not in urls:
                    urls.append(user_url)

                # from file watcher
                with open('urls.txt', 'a+') as f:
                    for line in f:
                        if line not in urls and line not in finished_urls:
                            urls.append(line)
                        if user_url is not None and user_url not in finished_urls:
                            f.write('\n' + user_url)


def updatedb():
    pages = {}

    urls = []
    with open('urls.txt') as f:
        for line in f:
            # urls if you want to print on start history
            urls.append(line)

    with WikiCrawler('wikipedia.db') as wc:
        # TODO: Store timestamps and update after X interval.
        for url in urls:            
            page = wc.retrieve(url)
            page['stats'] = parse_page(page)

            pages[page['title']] = page

            analyze_page(page)

    return pages


def oneshot(url):
    if WikiCrawler.wiki_regex.match(url):
        with WikiCrawler('wikipedia.db') as wc:            
            page = wc.retrieve(url)
            page['stats'] = parse_page(page)

            analyze_page(page)

        with open('urls.txt', 'a+') as f:
            if url not in f:
                f.write(url + '\n')    
    else: 
        print("Invalid URL!")


if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description="Digest wikipedia articles.")
    parser.add_argument('url', action='store', nargs='?', type=str, help="URL of wikipedia article to digest.")

    args = parser.parse_args()
    url = args.url

    if args.url:
        print(f"Looking up {args.url}...")
        oneshot(url)
    else:
        print("Updating db with urls.txt...")
        updatedb()

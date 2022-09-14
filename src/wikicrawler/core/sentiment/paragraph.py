#!/usr/bin/python

import time
import os
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

from ..sentiment.utils.dict_add import add_dict


console = Console()


fillerwords = ['at', 'their', 'been', 'which', 'on', 
                'was', 'also', 'from','we', 'can','the', 'of', 
                'and', 'is', 'a', 'that', 'to', 'as', 'in', 'are', 
                'or', 'not', 'by', 'be', 'it', "'s", 'i', 'for', 
                'with', 'an', 'has', 'have', 'some', 'were', 'but', 
                'this', 'its', 'such', 'who', 'his', 'her']

                
blacklist = ['!', "'", ':', '_', '\\', ',', '.', '(', ')', '{', '}', '``', "''", "[", "]"] + fillerwords


def get_sentiments(sentences):
    """ Sentiment analysis on a list of sentences.
    
    Returns a list of tuples of the form (word, score)
    """
    sia = SentimentIntensityAnalyzer()

    scores = []
    for sent in sentences:
        sent_score = sia.polarity_scores(sent)

        for word in nltk.word_tokenize(sent):
            word_score = sia.polarity_scores(word)
            scores.append((word, add_dict(sent_score, word_score, 0.5)))
     
    return scores


def print_sentiment(sentences):
    """ Pretty print sentiment analysis on a list of sentences.
    """
    # avg_score = { 'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0 }
    for word, score in get_sentiments(sentences):
        r = int(255*(score['neg']))
        g = int(255*(score['pos']))
        b = int(255*(score['neu']))
        c = int(127*(1+score['compound']))

        console.print(word, sep="", end=" ", style=f"rgb({r},{g},{b}) on rgb({c},{c},{c})", highlight=False)
    print()


def parse_page(page, level):
    """ Parse a page into a list of sentences, words, word frequencies, and collocations.
    """
    body = "".join(page['paragraphs'])
    sentences = nltk.sent_tokenize(body)
    words = nltk.word_tokenize(body)
    filtered_words = list(filter(lambda x: x.lower() not in blacklist and not x.isnumeric(), words))

    # n-grams
    filterstops = lambda w: len(w) < 3 or w in set(stopwords.words('english'))

    word_freq, bigrams, trigrams = None, [], []
    if level >= 1:
        word_freq = FreqDist(filtered_words)

    if level >= 2:
        bcf = BigramCollocationFinder.from_words(words)
        bcf.apply_word_filter(filterstops)

        bigrams = bcf.nbest(BigramAssocMeasures.likelihood_ratio, 15)

    if level >= 3:
        tcf = TrigramCollocationFinder.from_words(words)
        tcf.apply_word_filter(filterstops)
        tcf.apply_freq_filter(3)
        trigrams = tcf.nbest(TrigramAssocMeasures.likelihood_ratio, 10)

    collocs = bigrams + trigrams

    return body, sentences, words, word_freq, collocs


def analyze_page(page, amount=0.1, indices=None, level=2, printing=True):
    """ Prints a summary of parse_page() for a given page.

    Uses sentiment and collocation analysis to summarize a page.
    """
    # TODO: clean up use cases
    body, sentences, words, word_freq, collocs = parse_page(page, level)

    if printing:
        console.print(f"{'-'*80}\n[bold yellow]{page['title']} - {page['url']}[/bold yellow]")

        print(word_freq, f'\n[bold magenta]Collocations[/bold magenta]({[" ".join(entry) for entry in collocs]})\n')
        print("[bold magenta]Sentences[/bold magenta]\n\t[bold red]First 5:[/bold red]")
        print_sentiment(sentences[:5])

        tp_idx = int(.33*len(sentences))
        if indices is not None:
            tp_idx = indices[0]
            tp_stop = indices[1]
        else:
            if isinstance(amount, float) and amount <= 1.0:
                tp_stop = tp_idx + int(amount*len(sentences))
            elif isinstance(amount, int):
                tp_stop = tp_idx + amount
            else:
                tp_stop = tp_idx + 10

        print(f"\t[bold red]30% + {amount}:[/bold red]")
        print_sentiment(sentences[tp_idx:tp_stop])

        print("\t[bold red]Last 5:[/bold red]")
        print_sentiment(sentences[-5:])

    return body, sentences, words, word_freq, collocs


def analyze_pages(pages):
    structs = {}

    for title, page in pages.items():
       structs[title] = analyze_page(page)

    return structs
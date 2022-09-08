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


console = Console()


fillerwords = ['at', 'their', 'been', 'which', 'on', 
                'was', 'also', 'from','we', 'can','the', 'of', 
                'and', 'is', 'a', 'that', 'to', 'as', 'in', 'are', 
                'or', 'not', 'by', 'be', 'it', "'s", 'i', 'for', 
                'with', 'an', 'has', 'have', 'some', 'were', 'but', 
                'this', 'its', 'such', 'who', 'his', 'her']

                
blacklist = ['!', "'", ':', '_', '\\', ',', '.', '(', ')', '{', '}', '``', "''", "[", "]"] + fillerwords


def get_sentiments(sentences):
    sia = SentimentIntensityAnalyzer()

    sscores = []
    wscores = []
    for sent in sentences:
        sent_score = sia.polarity_scores(sent)

        for word in nltk.word_tokenize(sent):
            word_score = sia.polarity_scores(word)

            wscores.append((word, word_score))

        sscores.append(sent_score)

    return sscores, wscores


def print_sentiment(sentences):
    sscores, wscores = get_sentiments(sentences)

    # avg_score = { 'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0 }
    for sent, score in zip(sentences, sscores):
        # avg_score =  { 'neg': (avg_score['neg'] + score['neg']) * 0.5, 
        #                'neu': (avg_score['neu'] + score['neu']) * 0.5, 
        #                'pos': (avg_score['pos'] + score['pos']) * 0.5, 
        #                'compound': (avg_score['compound'] + score['compound']) * 0.5}
        
        r = int(255*(score['neg']))
        g = int(255*(score['pos']))
        b = int(255*(score['neu']))
        c = int(127*(1+score['compound']))

        for word, wscore in wscores:
            r2 = int(0.33*(r+2.0*int(255*(wscore['neg']))))
            g2 = int(0.33*(g+2.0*int(255*(wscore['pos']))))
            b2 = int(0.33*(b+2.0*int(255*(wscore['neu']))))
            c2 = int(0.33*(c+2.0*int(127*(1+wscore['compound']))))

            console.print(word, sep=" ", end=" ", style=f"rgb({r2},{g2},{b2}) on rgb({c2},{c2},{c2})", highlight=False)
    print()


def parse_page(page, level):
    body = " ".join(page['paragraphs'])
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


def analyze_page(page, level=2, printing=True):
    # todo: clean up use cases
    if not isinstance(page, tuple):
        body, sentences, words, word_freq, collocs = parse_page(page, level)
    else:
        body, sentences, words, word_freq, collocs = page

    if printing:
        console.print(f"{'-'*80}\n[bold yellow]{page['title']} - {page['url']}[/bold yellow]")

        print(word_freq, f'\n[bold magenta]Collocations[/bold magenta]({[" ".join(entry) for entry in collocs]})\n')
        print("[bold magenta]Sentences[/bold magenta]\n\t[bold red]First 5:[/bold red]")
        print_sentiment(sentences[:5])

        tp_idx = int(.33*len(sentences))
        print("\t[bold red]30% + 10:[/bold red]")
        print_sentiment(sentences[tp_idx:tp_idx+10])

        print("\t[bold red]Last 5:[/bold red]")
        print_sentiment(sentences[-5:])

    return word_freq, collocs


def analyze_pages(pages):
    structs = {}

    for title, page in pages.items():
       structs[title] = analyze_page(page)

    return structs
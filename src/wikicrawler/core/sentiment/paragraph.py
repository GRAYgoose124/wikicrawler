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


def analyze_page(page, level=2):
    body, sentences, words, word_freq, collocs = parse_page(page, level)

    console.print(f"{'-'*80}\n[bold yellow]{page['title']} - {page['url']}[/bold yellow]")

    print(word_freq, f'\n[bold magenta]Collocations[/bold magenta]({[" ".join(entry) for entry in collocs]})\n')
    print("[bold magenta]Sentences[/bold magenta]\n\t[bold red]First 5:[/bold red]")
    print_sentiment(sentences[:5])

    tp_idx = int(.33*len(sentences))
    print("\t[bold red]30% + 10:[/bold red]")
    print_sentiment(sentences[tp_idx:tp_idx+10])

    print("\t[bold red]Last 5:[/bold red]")
    print_sentiment(sentences[-5:])


def analyze_pages(pages):
    structs = {}

    for title, page in pages.items():
       structs[title] = analyze_page(page)

    return structs
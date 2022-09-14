# TODO: This is a hack because ['stats']['frequencies'] is a dict
# converted from a FreqDist so it can be pickled.
def get_highest_freq(freqs):
    max_freq = 0
    max_word = None

    for word, freq in freqs.items():
        if freq > max_freq:
            max_freq = freq
            max_word = word

    return max_word

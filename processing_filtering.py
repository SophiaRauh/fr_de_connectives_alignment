# -*- coding: utf-8 -*-

"""Filtering and Processing Data"""

import json
import pandas as pd
import string
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from copy import deepcopy

from nltk.tokenize import word_tokenize, RegexpTokenizer


def filter_most_common_conns(dictionary, word_threshold, phrase_threshold):
    """Removes alignments with a probability less than the threshold

    Parameters
    ----------
    dictionary : dict
        The alignment with probabilities
    threshold : float
        The minimum probability an alignment has to have

    Returns
    -------
    filtered : dict
        The alignment without the values less than the threshold
    """

    filtered = deepcopy(dictionary)
    for source, target in dictionary.items():
        for conn, count in target.items():
            if len(conn.split()) == 1:
                if count < word_threshold:
                    del filtered[source][conn]
            if len(conn.split()) > 1:
                if count < phrase_threshold:
                    del filtered[source][conn]

    return filtered


def alignment_probabilities(alignments):
    """Calculates the probalities of the alignments

    Parameters
    ----------
    alignments : dict
        A dictionary with uncounted and unsorted alignments

    Returns
    -------
    conn_alignments : dict
        A dictionary with the probability of each alignment
    """

    conn_alignments = dict()
    for key in alignments:
        try:
            conn_alignments[key] = Counter(alignments[key])
        except KeyError:
            continue

    for k, v in conn_alignments.items():
        exp = dict()
        for word, count in v.items():
            exp[word] = count / sum(v.values())
        conn_alignments[k] = exp

    return conn_alignments


def conn_count(alignments, lex):
    """Counts the connective alignments and sorts them

    Parameters
    ----------
    alignments : dict
        A dictionary that contains all alignments unsorted and uncounted
    lex : list
        A list with the connectives of a language

    Returns
    -------
    count : dict
        A dictionary with sorted and counted alignments
    """

    count = dict()
    for key in lex:
        try:
            count[key] = Counter(alignments[key])
        except KeyError:
            pass

    return count


def remove_low_counts(prob_dict, count_dict, word_count, phrase_count):
    """Removes the alignments with a number that is too low

    Parameters
    ----------
    prob_dict : dict
        The probabilities of alignments
    count_dict : dict
        The counts of alignments
    word_count : int
        The minimum number for an alignment (for single words)
    phrase_count : int
        The minimum number for an alignment (for phrases)

    Returns
    -------
    filtered_prob_dict : dict
        The probability alignment without the low numbers
    """

    filtered_prob_dict = deepcopy(prob_dict)

    for source, alignment in prob_dict.items():
        for target in alignment.keys():
            if len(target.split()) == 1:
                if count_dict[source][target] < word_count:
                    filtered_prob_dict[source].pop(target)
            else:
                if count_dict[source][target] < phrase_count:
                    filtered_prob_dict[source].pop(target)

    return filtered_prob_dict


def filter_unlikely_alignments(alignments, lang):
    """Removes alignments that are most likely incomplete or false

    Parameters
    ----------
    alignments : dict
        The probabilities of alignments
    lang : str
        "french" or "german"

    Returns
    -------
    alignments : dict
        The filtered probability alignment
    """

    if lang == "french":
        del_words = ["ich", "du", "er", "sie", "es", "wir", "ihr", "sie",
                     "das", "des", "die", "der", "einer", "eines", "eine",
                     "ist", "dem", "sich", "unseres", "ein"]
    elif lang == "german":
        del_words = ["l'", "ce"]

    for source in alignments.keys():
        singles = [single for single in alignments[source]
                   if len(single.split()) == 1]
        phrases = [phrase for phrase in alignments[source]
                   if len(phrase.split()) > 1]
        filtered_phrases = deepcopy(phrases)
        for phrase in phrases:
            if phrase.split()[-1] in del_words:
                del alignments[source][phrase]
                filtered_phrases.remove(phrase)

        for single in singles:
            if single in del_words and single in alignments[source]:
                del alignments[source][single]
            for phrase in filtered_phrases:
                if single in phrase.split() and single in alignments[source]\
                        and alignments[source][single] < 0.18:
                    del alignments[source][single]

        filtered_phr = deepcopy(filtered_phrases)
        for in_phrase in filtered_phr:
            for out_phrase in filtered_phr:
                if in_phrase != out_phrase\
                        and out_phrase in filtered_phrases\
                        and in_phrase in out_phrase\
                        and len(in_phrase.split()) != len(out_phrase.split())\
                        and in_phrase in alignments[source]\
                        and alignments[source][in_phrase] < 0.18\
                        and alignments[source][in_phrase]\
                        / alignments[source][out_phrase] < 3:
                    del alignments[source][in_phrase]
                    filtered_phrases.remove(in_phrase)

    return alignments


def remove_incomplete_phrases(alignments):
    """Removes phrases of the form "à ... occasion" if a complete
    phrase ("à l' occasion") exists

    Parameters
    ----------
    alignments : dict
        An already filtered alignment

    Returns
    -------
    filtered_alignments : dict
       The alignment without the incomplete phrases
    """

    filtered_alignments = deepcopy(alignments)

    for source, targets in alignments.items():
        for target in targets.keys():
            target_tokens = target.split()
            if len(target_tokens) >= 3 and "..." in target:
                for compare_target in targets.keys():
                    target_complete = compare_target.split()
                    clean_target = deepcopy(target_tokens)
                    clean_target.remove("...")
                    if len(target_complete) >= 3\
                            and "..." not in compare_target\
                            and target_tokens[0] == target_complete[0]\
                            and target_tokens[-1] == target_complete[-1]\
                            and all(map(str.isalpha, target_complete))\
                            and clean_target != target_complete:
                        try:
                            del filtered_alignments[source][target]
                        except KeyError:
                            pass

    return filtered_alignments


def filter_single_words(alignments, lang):
    """Removes false or incomplete (unrecognizable) alignments

    Parameters
    ----------
    alignments : dict
        The probabilities of alignments
    lang : str
        "french" or "german"

    Returns
    -------
    alignments : dict
        The filtered probability alignment
    """

    if lang == "french":
        del_words = ["dass", "wenn", "auf", "vor", "in", "mit"]
    elif lang == "german":
        del_words = ["avec", "dans", "devant", "par", "bien", "de",
                     "quoi", "même", "tout", "que", "qu'", "en", "est", "ce",
                     "sous", "qui", "s'", "si", "lors", "pendant", "durant"]

    for source in alignments.keys():
        single_words = [single for single in alignments[source]
                        if len(single.split()) == 1]
        single_words = pd.unique(single_words).tolist()

        for single in single_words:
            if single in del_words:
                del alignments[source][single]

    return alignments


def remove_pronouns(alignments, lang):
    """Removes alignments that contain a pronoun

    Parameters
    ----------
    alignments : dict
        An already filtered alignment
    lang : str
        The language of the keys

    Returns
    -------
    filtered_alignments : dict
        The same alignments without the phrases with pronouns
    """

    if lang == "german":
        pronouns = ["ich", "du", "er", "sie", "es", "wir", "ihr", "sie"]
    if lang == "french":
        pronouns = ["j'", "je", "tu", "il", "elle", "on", "nous", "vous",
                    "ils", "elles"]

    filtered_alignments = deepcopy(alignments)

    for source, targets in alignments.items():
        for target in targets.keys():
            target_tokens = target.split()
            if bool(set(pronouns) & set(target_tokens)):
                del filtered_alignments[source][target]

    return filtered_alignments


def remove_punct_phrases(tokens):
    """Removes punctuation in phrases

    ', weil' -> 'weil'
    Does not remove commas followed by 'dass' or 'daß'

    Parameters
    ----------
    tokens : list
        A list that contains a tokenized sentence

    Returns
    -------
    no_punct_phrases : list
        A list with the tokenized phrase without the punctuation
    tokens : list
        Unchanged list, if the list only contains one word
    """

    no_punct_phrases = tokens
    if len(tokens) > 1:
        if tokens[0] in string.punctuation:
            no_punct_phrases = tokens[1:]
        if tokens[-1] in string.punctuation:
            no_punct_phrases = no_punct_phrases[:-1]
        if no_punct_phrases:
            # '...' was used to indicate discontinuous phrases
            # If it just separated a comma from a word and is now at
            # the beginning or and of the phrase, it is deleted
            if no_punct_phrases[0] == "..." or no_punct_phrases[-1] == "...":
                no_punct_phrases.remove("...")
        return no_punct_phrases
    else:
        return tokens


def remove_punct_values(dictionary):
    """Replaces alignments to a punctuation with an empty string

    Removes ',', '.', etc. in values, but not ', weil'

    Parameters
    ----------
    dictionary : dict
        The unsorted and uncounted alignments

    Returns
    -------
    no_punct : dict
        The alignment without punctuation
    """

    no_punct = defaultdict(list)
    for source, target in dictionary.items():
        for word in target:
            if word and word in string.punctuation:
                no_punct[source].append("")
            else:
                no_punct[source].append(word)
    return no_punct


def json_to_dict(file):
    """Saves the alignment of the JSON file as a dictionary"""

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def read_fr_xml(doc):
    """Filters the ConnLex connectives

    Parameters
    ----------
    doc : str
        Path to the XML file for French connectives

    Returns
    -------
    fr_conn : list
        A list with the LexConn connectives
    """

    root = ET.parse(doc).getroot()
    fr_conn = []
    for entry in root.findall("./entry"):
        # Saves all variants of a connective
        # Single words and phrases (continuous)
        singles_phrases = [variant.text.lower() for variant
                           in entry.findall("./orths/orth[@type='cont']/part")]

        # Tokenization: "d'abord" -> "d' abord"
        tokenizer = RegexpTokenizer(r"\w*qu'|\w'|\w+(?:['-]\w+)*|[.,!?;]")
        singles_phrases = [" ".join(tokenizer.tokenize(phrase))
                           for phrase in singles_phrases]
        fr_conn += singles_phrases

        # Same procedure for discontinuous phrases
        for discont in entry.findall("./orths/orth[@type='discont']"):
            discontinuous = [part.text.lower() for part
                             in discont.findall("./part")]
            tokenizer = RegexpTokenizer(r"\w*qu'|\w'|\w+(?:['-]\w+)*|[.,!?;]")
            discontinuous = [" ".join(tokenizer.tokenize(phrase))
                             for phrase in discontinuous]
            discontinuous = " ... ".join(discontinuous)
            fr_conn.append(discontinuous)

    # Removes doubles which exist because everything is lower-case now
    fr_conn = pd.unique(fr_conn).tolist()

    return fr_conn


def read_de_xml(doc):
    """Filters the DimLex connectives

    Parameters
    ----------
    doc : str
        Path to the XML file for German connectives

    Returns
    -------
    de_conn : list
        A list with the DimLex connectives
    """

    de_conn = []
    root = ET.parse(doc).getroot()
    for entry in root.findall("./entry"):
        # Saves all variants of a connective
        # Single words and phrases (continuous)
        singles_phrases = [variant.text.lower() for variant
                           in entry.findall("./orths/orth[@type='cont']/part")]

        singles_phrases = [" ".join(word_tokenize(phrase, language="german"))
                           for phrase in singles_phrases]
        de_conn += singles_phrases

        # Same procedure for discontinuous phrases
        for discont in entry.findall("./orths/orth[@type='discont']"):
            discontinuous = [part.text.lower() for part
                             in discont.findall("./part")]
            discontinuous = [" ".join(word_tokenize(phrase, language="german"))
                             for phrase in discontinuous]
            discontinuous = " ... ".join(discontinuous)
            de_conn.append(discontinuous)

    # Removes doubles (because everything is lower-case now)
    de_conn = pd.unique(de_conn).tolist()
    de_conn.remove("z.b .")
    de_conn.remove("z.bsp .")
    de_conn.remove("d.h .")
    de_conn.append("z.b.")
    de_conn.append("z.bsp.")
    de_conn.append("d.h.")

    return de_conn


def save_alignments(file_name, content):
    """Saves a dictionary as a JSON file"""

    with open(file_name, "w",
              encoding="utf-8") as file:
        json.dump(content, file, indent=4,
                  sort_keys=True, ensure_ascii=False)


def remove_contractions(phrase, lang):
    """Looks at phrases that end with a contraction (preposition and
    article) and removes the article

    "... zur" -> "... zu"

    Parameters
    ----------
    phrase : list
        A phrase that ends with a contraction
    lang : str
        The language of the phrase

    Returns
    -------
    adjusted_phrase : str
        The same phrase without the article at the end
    """

    de = ["d'", "du", "des"]
    a = ["aux", "au"]
    zu = ["zur", "zum"]
    von = ["vom"]

    if lang == "french":
        if phrase[-1] in de:
            phrase[-1] = "de"
        if phrase[-1] in a:
            phrase[-1] = "à"
    if lang == "german":
        if phrase[-1] in zu:
            phrase[-1] = "zu"
        if phrase[-1] in von:
            phrase[-1] = "von"

    adjusted_phrase = " ".join(phrase)
    return adjusted_phrase


def complete_phrases(alignments, lex):
    """Completes phrases of the form "tout ... même" if a complete
    phrase ("tout de même") exists in the connective lexicon

    Parameters
    ----------
    alignments : dict
        An already filtered alignment

    Returns
    -------
    filtered : dict
       The alignment with completed phrases
    """

    filtered = deepcopy(alignments)

    for source, targets in alignments.items():
        for target in targets.keys():
            target_tokens = target.split()
            if len(target_tokens) >= 3 and "..." in target:
                for compare_conn in lex:
                    target_complete = compare_conn.split()
                    clean_target = deepcopy(target_tokens)
                    clean_target.remove("...")
                    if len(target_complete) >= 3\
                            and "..." not in compare_conn\
                            and target_tokens[0] == target_complete[0]\
                            and target_tokens[-1] == target_complete[-1]\
                            and all(map(str.isalpha, target_complete))\
                            and clean_target != target_complete:
                        try:
                            probability = filtered[source].pop(target)
                            filtered[source][compare_conn] = probability
                        except KeyError:
                            pass

    return filtered

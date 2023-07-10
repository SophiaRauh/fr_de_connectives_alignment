# -*- coding: utf-8 -*-

"""Parse Word Alignments"""

import argparse
from collections import defaultdict

import pandas as pd

from processing_filtering import (remove_contractions, save_alignments,
                                  remove_punct_phrases)


def parse_alignments(result, german_sentences, french_sentences):
    """Creates alignments for single words, phrases and discontinous
    phrases based on the word alignment

    Parameters
    ----------
    result : str
        The file name for the word alignment
    german_sentences : str
        The file name for the German corpus
    french_sentences : str
        The file name for the French corpus

    Returns
    -------
    de_fr_alignments: defaultdict
        A dictionary with German keys and the French alignments as
        values
    fr_de_alignments: defaultdict
        A dictionary with French keys and the German alignments as
        values
    """

    de_fr_alignments = defaultdict(list)
    fr_de_alignments = defaultdict(list)

    with open(result, "r", encoding="utf-8") as result,\
            open(german_sentences, "r", encoding="utf-8") as german,\
            open(french_sentences, "r", encoding="utf-8") as french:
        for index, de, fr in zip(result, german, french):
            german = de.split()
            french = fr.split()
            alignment = index.split()
            pair = [[a.split("-")[0], a.split("-")[1]] for a in alignment]

            # Adds an empty string as alignment if there is no
            # alignment for a word
            de_missing = list(range(0, len(german)))
            fr_missing = list(range(0, len(french)))
            for word1, word2 in pair:
                try:
                    de_missing.remove(int(word1))
                except ValueError:
                    pass
                try:
                    fr_missing.remove(int(word2))
                except ValueError:
                    pass

            if de_missing:
                for m in de_missing:
                    de_fr_alignments[german[m]].append("")
            if fr_missing:
                for m in fr_missing:
                    fr_de_alignments[french[m]].append("")

            # Adds the alignments to dictionaries so that phrases
            # are allowed as well
            phrase_align_fr_r = defaultdict(list)
            phrase_align_de_r = defaultdict(list)
            for p in pair:
                phrase_align_fr_r[p[1]].append(p[0])
                phrase_align_de_r[p[0]].append(p[1])

            # The dictionary is reversed so that phrases are possible
            # for both directions
            phrase_align_de = defaultdict(list)
            phrase_align_fr = defaultdict(list)
            for k, v in phrase_align_fr_r.items():
                phrase_align_de[tuple(v)].append(k)
            for k, v in phrase_align_de_r.items():
                phrase_align_fr[tuple(v)].append(k)

            # Identifies discontinous phrases
            # However, seems more like alignment errors
            # For German - French
            for k, v in phrase_align_de.items():
                if len(v) > 1:
                    for pos in range(len(v)-1):
                        if v[pos].isnumeric() and v[pos+1].isnumeric():
                            if abs(int(v[pos]) - int(v[pos+1])) > 1:
                                phrase_align_de[k].insert(pos+1, "...")

            # For French - German
            for k, v in phrase_align_fr.items():
                if len(v) > 1:
                    for pos in range(len(v)-1):
                        if v[pos].isnumeric() and v[pos+1].isnumeric():
                            if abs(int(v[pos]) - int(v[pos+1])) == 2:
                                if german[int(v[pos])+1] == ",":
                                    phrase_align_fr[k].insert(pos+1, ",")
                                else:
                                    phrase_align_fr[k].insert(pos+1, "...")
                            elif abs(int(v[pos]) - int(v[pos+1])) > 2:
                                phrase_align_fr[k].insert(pos+1, "...")

            # Index is replaced by the corresponding word
            for de, fr in phrase_align_de.items():
                k = ([german[int(i)] if i.isnumeric() else i for i in de])
                v = ([french[int(i)] if i.isnumeric() else i for i in fr])
                k = remove_punct_phrases(k)
                v = remove_punct_phrases(v)
                contractions = ["d'", "du", "des", "aux", "au"]
                if v and v[-1] in contractions:
                    v = remove_contractions(v, "french")
                de_fr_alignments[" ".join(k)].append(" ".join(v))

            for fr, de in phrase_align_fr.items():
                k = ([french[int(i)] if i.isnumeric() else i for i in fr])
                v = ([german[int(i)] if i.isnumeric() else i for i in de])
                k = remove_punct_phrases(k)
                v = remove_punct_phrases(v)
                contractions = ["zur", "zum", "vom"]
                if v and v[-1] in contractions:
                    v = remove_contractions(v, "german")
                fr_de_alignments[" ".join(k)].append(" ".join(v))

    return de_fr_alignments, fr_de_alignments


def parse_phrase_alignments(result, language1, language2, phrases, lang=1):
    """Creates alignments for phrases independently from the word
    alignment

    Can be used in case phrases were separated: "abgesehen" and "davon"
    could be aligned as single words to two different french words.
    However, both might be phrases that are expressed with a similar
    structure.

    Parameters
    ----------
    result : str
        The file name for the word alignment
    language1 : str
        The file name for the source language
    language2 : str
        The file name for the target language
    phrases : list
        A list with all phrases of language 1 or 2
    lang : int
        An integer that indicates whether the phrases correspond to
        language 1 or 2

    Returns
    -------
    phrase_alignments : defaultdict
        A dictionary with the alignments for phrases
    """

    de_fr_count = defaultdict(int)
    fr_de_count = defaultdict(int)

    phrase_alignments = defaultdict(list)
    with open(result, "r", encoding="utf-8") as result,\
            open(language1, "r", encoding="utf-8") as lang1,\
            open(language2, "r", encoding="utf-8") as lang2:
        for index, l1, l2 in zip(result, lang1, lang2):
            lang_1 = l1.split()
            lang_2 = l2.split()
            alignment = index.split()
            pair = [[int(a.split("-")[0]), int(a.split("-")[1])]
                    for a in alignment]
            if lang == 1:
                sentence = l1
                source_tok = lang_1
                target_tok = lang_2
            elif lang == 2:
                sentence = l2
                source_tok = lang_2
                target_tok = lang_1

            for phrase_ in phrases:
                if phrase_ in sentence:
                    phrase = phrase_.split()
                    # Index of the phrase words in the source language
                    phrase_index = []
                    # Searches the exact position of the phrase in the
                    # string
                    # Might occur more than once, although unlikely
                    for pos in range(0, len(source_tok) - len(phrase) + 1):
                        if source_tok[pos:pos+len(phrase)] == phrase:
                            phrase_index.append(list(range(pos,
                                                           pos + len(phrase))))

                    for pos_range in phrase_index:
                        # Indexes of the target words
                        new_phrase = []
                        for word_pos in pos_range:
                            # Saves all target indexes in a list
                            if lang == 1:
                                alignment_index = [i2 for i1, i2 in pair
                                                   if i1 == word_pos]
                            elif lang == 2:
                                alignment_index = [i1 for i1, i2 in pair
                                                   if i2 == word_pos]
                            new_phrase += alignment_index
                        new_phrase = pd.unique(new_phrase).tolist()
                        if len(new_phrase) > 1:
                            new_phrase.sort()
                            # Inserts "..." for discontinuous
                            # phrases
                            pos = 0
                            while pos < len(new_phrase) - 1:
                                if isinstance(new_phrase[pos], int)\
                                        and isinstance(new_phrase[pos+1], int):
                                    if abs(new_phrase[pos]
                                           - new_phrase[pos+1]) == 2:
                                        if target_tok[new_phrase[pos]+1]\
                                                == ",":
                                            new_phrase.insert(pos+1, ",")
                                        else:
                                            new_phrase.insert(pos+1, "...")
                                    elif abs(new_phrase[pos]
                                             - new_phrase[pos+1]) > 2:
                                        new_phrase.insert(pos+1, "...")
                                pos += 1
                        # Index is replaced by the corresponding word
                        new_phrase = [target_tok[pos] if isinstance(pos, int)
                                      else pos
                                      for pos in new_phrase]
                        new_phrase = remove_punct_phrases(new_phrase)
                        contractions = ["d'", "du", "des", "aux", "au", "zur",
                                        "zum", "vom"]
                        if new_phrase and new_phrase[-1] in contractions:
                            if lang == 1:
                                new_phrase = remove_contractions(new_phrase,
                                                                 "french")
                            else:
                                new_phrase = remove_contractions(new_phrase,
                                                                 "german")
                        else:
                            new_phrase = " ".join(new_phrase)
                        if ", ..." in new_phrase:
                            new_phrase = new_phrase.replace(", ...", "...")
                        phrase_alignments[phrase_].append(new_phrase)
                        if lang == 1:
                            de_fr_count[phrase_] += 1
                        else:
                            fr_de_count[phrase_] += 1

    return phrase_alignments


def parse_discontinuous(result, language1, language2, phrases, lang=1):
    """Creates alignments for phrases independently from the word
    alignment

    Can be used in case phrases were separated: "abgesehen" and "davon"
    could be aligned as single words to two different french words.
    However, both might be phrases that are expressed with a similar
    structure.

    Parameters
    ----------
    result : str
        The file name for the word alignment
    language1 : str
        The file name for the source language
    language2 : str
        The file name for the target language
    phrases : list
        A list with all phrases of language 1 or 2
    lang : int
        An integer that indicates whether the phrases correspond to
        language 1 or 2

    Returns
    -------
    phrase_alignments : defaultdict
        A dictionary with the alignments for phrases
    """

    de_fr_count = defaultdict(int)
    fr_de_count = defaultdict(int)

    phrase_alignments = defaultdict(list)
    with open(result, "r", encoding="utf-8") as result,\
            open(language1, "r", encoding="utf-8") as lang1,\
            open(language2, "r", encoding="utf-8") as lang2:
        for index, l1, l2 in zip(result, lang1, lang2):
            lang_1 = l1.split()
            lang_2 = l2.split()
            alignment = index.split()
            pair = [[int(a.split("-")[0]), int(a.split("-")[1])]
                    for a in alignment]
            if lang == 1:
                sentence = l1
                source_tok = lang_1
                target_tok = lang_2
            elif lang == 2:
                sentence = l2
                source_tok = lang_2
                target_tok = lang_1

            for phrase_ in phrases:
                phrase = phrase_.split(" ... ")
                if phrase[0] in sentence\
                        and phrase[1] in sentence\
                        and sentence.index(phrase[0])\
                        < sentence.index(phrase[1]):
                    # Index of the phrase words in the source language
                    phrase_index = []
                    # Searches the exact position of the phrase in the
                    # string
                    # Might occur more than once, although unlikely
                    for part in phrase:
                        part = part.split()
                        for pos in range(0, len(source_tok) - len(part) + 1):
                            if source_tok[pos:pos+len(part)] == part:
                                source_pos = list(range(pos, pos
                                                        + len(part)))
                                if source_pos not in phrase_index:
                                    phrase_index.append(source_pos)
                                    break

                    new_phrase = []
                    for pos_range in phrase_index:
                        # Indexes of the target words
                        for word_pos in pos_range:
                            # Saves all target indexes in a list
                            if lang == 1:
                                alignment_index = [i2 for i1, i2 in pair
                                                   if i1 == word_pos]
                            elif lang == 2:
                                alignment_index = [i1 for i1, i2 in pair
                                                   if i2 == word_pos]
                            new_phrase += alignment_index

                    new_phrase = pd.unique(new_phrase).tolist()
                    if len(new_phrase) > 1:
                        new_phrase.sort()
                        # Inserts "..." for discontinuous phrases
                        pos = 0
                        while pos < len(new_phrase) - 1:
                            if isinstance(new_phrase[pos], int)\
                                    and isinstance(new_phrase[pos+1], int):
                                if abs(new_phrase[pos]
                                       - new_phrase[pos+1]) == 2:
                                    if target_tok[new_phrase[pos]+1]\
                                            == ",":
                                        new_phrase.insert(pos+1, ",")
                                    else:
                                        new_phrase.insert(pos+1, "...")
                                elif abs(new_phrase[pos]
                                         - new_phrase[pos+1]) > 1:
                                    new_phrase.insert(pos+1, "...")
                            pos += 1
                    # Index is replaced by the corresponding word
                    new_phrase = [target_tok[pos] if isinstance(pos, int)
                                  else pos
                                  for pos in new_phrase]
                    new_phrase = remove_punct_phrases(new_phrase)
                    contractions = ["d'", "du", "des", "aux", "au", "zur",
                                    "zum", "vom"]
                    if new_phrase and new_phrase[-1] in contractions:
                        if lang == 1:
                            new_phrase = remove_contractions(new_phrase,
                                                             "french")
                        else:
                            new_phrase = remove_contractions(new_phrase,
                                                             "german")
                    else:
                        new_phrase = " ".join(new_phrase)
                    if ", ..." in new_phrase:
                        new_phrase = new_phrase.replace(", ...", "...")
                    phrase_alignments[phrase_].append(new_phrase)
                    if lang == 1:
                        de_fr_count[phrase_] += 1
                    else:
                        fr_de_count[phrase_] += 1

    return phrase_alignments


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("word_alignment",
                        help="Alignment text file in Pharaoh format")
    parser.add_argument("german_corpus", help="Corpus with German sentences")
    parser.add_argument("french_corpus", help="Corpus with French sentences")
    args = parser.parse_args()
    german, french = parse_alignments(args.word_alignment, args.german_corpus,
                                      args.french_corpus)
    save_alignments("de_word_alignment.json", german)
    save_alignments("fr_word_alignment.json", french)

# -*- coding: utf-8 -*-

"""Connectives Alignment"""

from collections import defaultdict

from processing_filtering import (filter_most_common_conns, remove_pronouns,
                                  alignment_probabilities, conn_count,
                                  remove_low_counts, complete_phrases,
                                  filter_unlikely_alignments,
                                  remove_incomplete_phrases,
                                  filter_single_words, remove_punct_values)
from parse_all_alignments import parse_phrase_alignments, parse_discontinuous


class FindAlignments:
    """A class used to find new alignments to connectives in French and
    German

    Parameters
    ----------
    de_alignment_file : defaultdict or str
        Dictionary or file with German - French alignments
    fr_alignment_file : defaultdict or str
        Dictionary or file with French - German alignments
    alignment : str
        Path to the alignment (format: 1-1 1-2 ...)
    german_corpus : str
        Path to the German corpus
    french_corpus : str
        Path to the French corpus
    fr_lex : list
        LexConn connectives filtered for a discourse relation type
    de_lex : list
        DimLex connectives filtered for a discourse relation type
    all_fr_conns : list
        LexConn connectives unfiltered
    all_de_conns : list
        DimLex connectives unfiltered

    Attributes
    ----------
    de_fr : dict
        German - French alignment (unsorted, uncounted)
    fr_de : dict
        French - German alignment (unsorted, uncounted)
    alignment : str
        Path to the alignment (format: 1-1 1-2 ...)
    german_corpus : str
        Path to the German corpus
    french_corpus : str
        Path to the French corpus
    fr_lex : list
        LexConn connectives filtered for a discourse relation type
    de_lex : list
        DimLex connectives filtered for a discourse relation type
    all_fr_conns : list
        LexConn connectives unfiltered
    all_de_conns : list
        DimLex connectives unfiltered
    counter : int
        counts the rounds to find new alignments
    de_conn_alignments: dict
        German alignments (filtered, as probabilities)
    fr_conn_alignments: dict
        French alignments (filtered, as probabilities)
    de_count : dict
        German alignments (unfiltered, as counts)
    fr_count : dict
        French alignments (unfiltered, as counts)
    """

    def __init__(self, de_alignment_file, fr_alignment_file, alignment,
                 german_corpus, french_corpus, de_lex, fr_lex, all_de_conns,
                 all_fr_conns):
        self.de_fr = de_alignment_file
        self.fr_de = fr_alignment_file
        self.alignment = alignment
        self.german_corpus = german_corpus
        self.french_corpus = french_corpus
        self.fr_lex = fr_lex
        self.de_lex = de_lex
        self.all_de_conns = all_de_conns
        self.all_fr_conns = all_fr_conns
        self.counter = 0
        self.de_conn_alignments = dict()
        self.fr_conn_alignments = dict()
        self.de_count = dict()
        self.fr_count = dict()

    def find_conns(self, lex=[], lang="german", word_threshold=0.02,
                   phrase_threshold=0.02, word_min_count=20,
                   phrase_min_count=10, limit=1):
        """Finds new connective alignments

        Parameters
        ----------
        lex : list
            The lexicon used to find new alignments (German or French)
        lang : str
            The language set to French or German
        word_threshold : float
            The minimum probability for an alignment for a single word
        phrase_threshold : float
            The minimum probability for an alignment for a phrase
        word_min_count : int
            The minimum number for an alignment for a single word
        phrase_min_count : int
            The minimum number for an alignment for a phrase
        limit : int
            The number of rounds

        Returns
        -------
        None
        """

        self.counter += 1

        if lang == "french":
            alignments = self.fr_de
            count_dict = self.fr_count
            lang_pos = 2
            other_lang = "german"
            if not lex:
                lex = self.fr_lex
            # Delete connectives with inaccurate alignment
            fr_del = ["dire que", "dire qu'", "et dire que", "et dire qu'",
                      "encore que", "cependant que", "cependant qu'",
                      "encore qu'", "si", "s'",
                      "en même temps que", "en même temps qu'"]
            lex = [conn for conn in lex if conn not in fr_del]

            other_lex = self.de_lex
            complete_lex = self.all_de_conns
        elif lang == "german":
            alignments = self.de_fr
            count_dict = self.de_count
            lang_pos = 1
            other_lang = "french"
            if not lex:
                lex = self.de_lex
            # Delete connectives with inaccurate alignment
            de_del = ["bloß", "dabei", "mangels", "mithin", "obschon",
                      "wenn ... auch", "wiederum", "wobei", "wohingegen",
                      "als ob"]
            lex = [conn for conn in lex if conn not in de_del]
            other_lex = self.fr_lex
            complete_lex = self.all_fr_conns
        else:
            pass

        new_conns = []
        new_alignments = defaultdict(list)
        # Find all alignments for the current connective lexicon
        single_words = [word for word in lex if len(word.split()) == 1]
        phrases = [phrase for phrase in lex if len(phrase.split()) > 1
                   and "..." not in phrase]
        discontinuous = [phrase for phrase in lex if "..." in phrase]

        for key in single_words:
            try:
                new_alignments[key] = alignments[key]
            except KeyError:
                pass

        new_phrase_alignments = parse_phrase_alignments(
            self.alignment, self.german_corpus, self.french_corpus,
            phrases, lang=lang_pos)

        new_discontinuous = parse_discontinuous(
            self.alignment, self.german_corpus, self.french_corpus,
            discontinuous, lang=lang_pos)

        single_count = conn_count(new_alignments, lex)
        phrase_count = conn_count(new_phrase_alignments, phrases)
        discont_count = conn_count(new_discontinuous, discontinuous)
        if lang == "french":
            self.fr_count.update(single_count)
            self.fr_count.update(phrase_count)
            self.fr_count.update(discont_count)
        elif lang == "german":
            self.de_count.update(single_count)
            self.de_count.update(phrase_count)
            self.de_count.update(discont_count)

        # Combine the single word and phrase alignments
        new_alignments = {**new_alignments, **new_phrase_alignments,
                          **new_discontinuous}
        new_alignments = remove_punct_values(new_alignments)
        new_alignments = alignment_probabilities(new_alignments)
        new_alignments = filter_most_common_conns(new_alignments,
                                                  word_threshold,
                                                  phrase_threshold)
        new_alignments = remove_low_counts(new_alignments, count_dict,
                                           word_min_count, phrase_min_count)
        new_alignments = filter_unlikely_alignments(new_alignments, lang)
        new_alignments = remove_incomplete_phrases(new_alignments)
        new_alignments = filter_single_words(new_alignments, lang)
        new_alignments = remove_pronouns(new_alignments, other_lang)
        new_alignments = complete_phrases(new_alignments, complete_lex)

        # Find new connectives
        for conns in new_alignments.values():
            for word, count in conns.items():
                if word and word not in other_lex:
                    new_conns.append(word)
        new_conns = list(set(new_conns))

        if lang == "french":
            self.fr_conn_alignments.update(new_alignments)
            self.de_lex += new_conns
            lex = self.de_lex
            lang = "german"
        else:
            self.de_conn_alignments.update(new_alignments)
            self.fr_lex += new_conns
            lex = self.fr_lex
            lang = "french"

        if self.counter == limit:
            return

        if self.counter == 1:
            # Ensures that the first entries of the lexicon (DimLex or
            # LexConn) are not ignored
            self.find_conns(lex, lang, word_threshold, phrase_threshold,
                            word_min_count, phrase_min_count, limit)
        else:
            self.find_conns(new_conns, lang, word_threshold, phrase_threshold,
                            word_min_count, phrase_min_count, limit)

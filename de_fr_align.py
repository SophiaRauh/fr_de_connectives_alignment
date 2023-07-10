# -*- coding: utf-8 -*-

"""Organising the Output: Connectives Alignments and Visual Output"""

import argparse
from pathlib import Path

from conn_search import FindAlignments
from discourse_relations import (filter_for_discourse_relation,
                                 add_discourse_relation,
                                 discourse_relation_mapping,
                                 create_sankey_diagram)
from processing_filtering import (json_to_dict, read_de_xml, read_fr_xml,
                                  save_alignments)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("word_alignment",
                        help="Alignment text file in Pharaoh format")
    parser.add_argument("german_corpus", help="Corpus with German sentences")
    parser.add_argument("french_corpus", help="Corpus with French sentences")
    parser.add_argument("-dr", "--discourse_relation", type=str,
                        default="concession",
                        help="The discourse relation (e.g. 'concession')")
    parser.add_argument("-s", "--show_relation", action="store_true",
                        help="If specified, connectives are saved with"
                        " corresponding discourse relation")
    parser.add_argument("-wt", "--word_threshold", action="store",
                        default=0.021, type=float,
                        help="Relative word threshold in percent")
    parser.add_argument("-pt", "--phrase_threshold", action="store",
                        default=0.014, type=float,
                        help="Relative phrase threshold in percent")
    parser.add_argument("-i", "--iterations", action="store",
                        default=3, type=int, help="Number of iterations")
    parser.add_argument("-wc", "--word_count", action="store",
                        default=20, type=int,
                        help="Absolute word threshold as count")
    parser.add_argument("-pc", "--phrase_count", action="store",
                        default=10, type=int,
                        help="Absolute phrase threshold as count")
    parser.add_argument("-g", "--german_first", action="store_true",
                        help="If specified, the first iteration starts with"
                        " German-French, default is French-German")

    args = parser.parse_args()

    if args.german_first:
        language = "german"
    else:
        language = "french"

    german_word_alignment = json_to_dict("de_word_alignment.json")
    french_word_alignment = json_to_dict("fr_word_alignment.json")

    lexconn = read_fr_xml(Path("connectives_and_relations/lexconn_d.xml"))
    dimlex = read_de_xml(Path("connectives_and_relations/dimlex.xml"))
    de_rel = json_to_dict(Path("connectives_and_relations/de_relations.json"))
    fr_rel = json_to_dict(Path("connectives_and_relations/fr_relations.json"))
    rel = json_to_dict(Path("connectives_and_relations/relations.json"))

    if args.discourse_relation:
        fr_lex = filter_for_discourse_relation(lexconn, fr_rel,
                                               args.discourse_relation, rel)
        de_lex = filter_for_discourse_relation(dimlex, de_rel,
                                               args.discourse_relation, rel)
    else:
        fr_dex = lexconn
        de_lex = dimlex

    align = FindAlignments(german_word_alignment, french_word_alignment,
                           Path(args.word_alignment),
                           Path(args.german_corpus), Path(args.french_corpus),
                           de_lex, fr_lex, dimlex, lexconn)

    align.find_conns(lang=language, word_threshold=args.word_threshold,
                     phrase_threshold=args.phrase_threshold,
                     word_min_count=args.word_count,
                     phrase_min_count=args.phrase_count, limit=args.iterations)

    if args.show_relation:
        fr_alignment = add_discourse_relation(align.fr_conn_alignments, fr_rel,
                                              de_rel)
        de_alignment = add_discourse_relation(align.de_conn_alignments, de_rel,
                                              fr_rel)
    else:
        fr_alignment = align.fr_conn_alignments
        de_alignment = align.de_conn_alignments

    if fr_alignment:
        save_alignments(
            f"fr_de_connectives_alignment_{args.discourse_relation}.json",
            fr_alignment)
        fr_mapping = discourse_relation_mapping(align.fr_conn_alignments,
                                                fr_rel, de_rel)
        create_sankey_diagram(fr_mapping, "fr", "de", args.discourse_relation,
                              f"fr_de_{args.discourse_relation}_mapping.png")
    if de_alignment:
        save_alignments(
            f"de_fr_connectives_alignment_{args.discourse_relation}.json",
            de_alignment)
        de_mapping = discourse_relation_mapping(align.de_conn_alignments,
                                                de_rel, fr_rel)
        create_sankey_diagram(de_mapping, "de", "fr", args.discourse_relation,
                              f"de_fr_{args.discourse_relation}_mapping.png")

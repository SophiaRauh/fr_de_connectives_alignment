# Aligning German/French Connectives
This program can be used to extract the word alignment based on a file in pharaoh format and to align French and German connectives.

## Installation
The project is written with Python 3. Further requirements are:
* nltk
* pandas
* plotly

The required version can be found in **requirements.txt**.

## Usage
#### 1. Extracting the word alignment
Based on a text file with the word alignment in pharaoh format and a parallel corpus, two JSON files with the alignments for French-German and German-French are generated. Both files are required for the alignment of connectives and they are automatically saved in the same directory as the code.
```
python parse_all_alignments.py [-h] word_alignment german_corpus french_corpus
```
| Positional Arguments | Explanation|
|----------|-------------------------------|
| _word\_alignment_ |  TXT file with word alignment in pharaoh format |
| _german\_corpus_ | Path to the corpus with German sentences as TXT file |
| _french\_corpus_ | Path to the corpus with French sentences as TXT file |

| Optional Arguments | Explanation| Example |
|----------|-------------------------------|-----|
| _-h, --help_ | Show this help message and exit | -h |

##### Example
```
python parse_all_alignments.py de_fr_alignment.txt german_corpus.txt french_corpus.txt
```

#### 2. Alignment of Connectives
This file computes the alignment of French-German connectives of one chosen discourse relation. The connectives alignments are saved as JSON files and two sankey diagrams with the mapping of the discourse relations are created.
```
python de_fr_align.py [-h] [-dr DISCOURSE_RELATION] [-s] [-wt WORD_THRESHOLD]
                      [-pt PHRASE_THRESHOLD] [-i ITERATIONS] [-wc WORD_COUNT]
                      [-pc PHRASE_COUNT] [-g]
                      word_alignment german_corpus french_corpus

```
| Positional Arguments | Explanation|
|----------|-------------------------------|
| _word\_alignment_ |  TXT file with word alignment in pharaoh format |
| _german\_corpus_ | Path to the corpus with German sentences as TXT file |
| _french\_corpus_ | Path to the corpus with French sentences as TXT file |

| Optional Arguments | Explanation| Example |
|----------|-------------------------------|-----|
| _-h_ | Show this help message and exit | -h |
| _-dr_ | Discourse relation of the connectives alignment | -dr cause |
| _-s_ |  If specified, connectives are saved with corresponding discourse relation | -s |
| _-wt_ | Relative word threshold in percent | -wt 0.03 |
| _-pt_ | Relative threshold for phrases in percent | -pt 0.02 |
| _-i_ | Number of iterations | -i 2 |
| _-wc_ | Absolute word threshold as count | -wc 40 |
| _-pc_ |  Absolute phrase threshold as count | -pc 20 |
| _-g_ | If specified, the first iteration starts with German-French, default is French-German | -g |

__Discourse relations that can be used:__
contrast, similarity, concession, cause, condition, negative-condition, purpose, conjunction, disjunction, equivalence, instantiation, level-of-detail, substitution, exception, manner, synchronous, asynchronous

If no relation is specified, concession is chosen as a default.

##### Example
```
python de_fr_align.py -dr contrast alignment.txt german.txt french.txt
```


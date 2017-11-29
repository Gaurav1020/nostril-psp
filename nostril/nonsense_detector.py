#!/usr/bin/env python3
'''Detect nonsense/garbage strings.

Introduction
------------

This module implements a mechanism to infer whether a given word or text
string is likely to be meaningful or nonsense.  In the context of our
CASICS system, the main use case is to decide whether strings returned by
source code mining methods are likely to be (e.g.) program identifiers, or
random characters or other non-identifier strings.  The function generated
by this system takes a text string and returns True if it is probably
nonsense, False otherwise (if it likely to be meaningful).

Usage
-----

The basic usage is very simple.  Nostril is a Python module that (among
other things) provides a function named is_nonsense().  This function takes
a text string as an argument and returns a Boolean value as a result.  Here
is an example:

    from nostril import is_nonsense
    result = is_nonsense('yoursinglestringhere')

The value of result will be a Boolean, with the value True if the input
string is probably meaningless and False if it is probably not.  (Note: the
first time you import the module nostril, it will take extra time because
Nostril loads a large data file during the import step.  If you only execute
the short two-line example above, it will seem that Nostril takes far too
long to evaluate a string.  This is misleading: one it's loaded, multiple
calls to is_nonsense() are very fast.)

It is possible to tune some of the parameters used by the classifier.  The
parameters are part of the mathematical function used internally by Nostril
to compute a score for a given input string.  To get a pointer to a new
classifier function (a closure) with different values of the tunable
parameters, call generate_nonsense_detector like so:

    from nostril import generate_nonsense_detector
    is_nonsense = generate_nonsense_detector(...)

where "..." are parameters that are explained in the help string.  The new
function is_nonsense() obtained by calling the generator this way can be used
exactly as the default version of is_nonsense():

    result = is_nonsense('yoursinglestringhere')

Internally, Nostril uses a table of precomputed n-gram weights that were
derived by training the system on data sets of labeled test cases.  A saved
copy of the trained values are stored in this directory, so that it is not
necessary to retrain the system to adjust the tunable parameters.  However,
it is also possible to retrain the system and recompute the n-gram weights.
This process is somewhat more involved, and discussed below.

Known limitations
-----------------

Nostril is not fool-proof; it _will_ generate some false positive and false
negatives.  This is an unavoidable consequence of the problem domain: without
special knowledge, even a human cannot recognize a real text string in all
cases.  Nostril's default trained system puts emphasis on reducing false
positives (i.e., reducing how often it mistakenly labels something as
nonsense) rather than false negatives, so it will sometimes report that
something is not nonsense when it really is.  With its default parameter
values, on dictionary words (specifically, 218,752 words from
`/usr/share/dict/web2`), the default version of `is_nonsense()` achieves
greater than 99.99% accuracy.  In tests on real identifiers extracted from
actual software source code, it achieves 99.94% to 99.96% accuracy; on truly
random strings, it achieves 86% accuracy.  Inspecting the errors shows that
most false positives really are quite ambiguous, to the point where most
false positives are random-looking, and many false negatives could be
plausible identifiers.

A vexing result is that this system does more poorly on "random" strings
typed by a human.  In a data set of 1000 strings "typed at random" by the
author, it achieves only 67% accuracy.  I hypothesize this is because those
strings may be less random than they seem: if someone is asked to type junk
at random on a QWERTY keyboard, they are likely to use a lot of characters
from the home row (a-s-d-f-g-h-j-k-l), and those actually turn out to be
rather common in English words.  In other words, what we think of a strings
"typed at random" on a keyboard are actually not that random, and probably
have statistical properties similar to those of real words.  These cases are
hard for Nostril, but thankfully, in real-world situations, they are rare.
This view is supported by the fact that Nostril's performance is much better
on statistically random text strings generated by software.

Finally, the algorithm does not perform well on very short text, and by
default, Nostril imposes a lower length limit of 6 characters &ndash; strings
have to be longer than 6 characters or else it will raise an exception.

Operating principles
--------------------

The method currently used uses letter n-grams scored by a custom TF-IDF (term
frequency - inverse document frequency) scheme.  The nonsense detector
uses precomputed n-gram weights stored in a large array, and when testing a
string, it combines the values of the scores for the string using a custom
mathematical formula.  If the formula value exceeds a fixed threshold, the
string is rated as being nonsense.  To make an analogy to how TF-IDF is used
in document classification, nonsense strings are those that use unusual
n-grams and thus score highly, while real/meaningful strings are those that
use more common n-grams and thus score lower.

There are some minor innovations here in the way that the TF-IDF scores are
calculated.  First, empty n-grams in the n-gram frequency table (meaning,
n-grams that were never seen during training) are given high values to
reflect the fact that they are unusual.  Second, a power function is
applied to repeated n-grams in a string, to raise the score of strings that
contain embedded repeats of the same pattern: i.e., things like
"SomethingHellohellohellohellohellohello" -- it contains real words (not
random characters) yet probably does not represent a meaningful identifier.
(Strings like this would otherwise not score highly because they match
common n-grams.)  Finally, there is a length-dependent factor applied to
strings longer than about 28 characters, such that a string's score is
raised slowly the longer the string is past 28 characters.  This helps
detect very long strings that happen to use common n-grams *without*
repeats: while long identifiers are not that unusual in programming
contexts, the longer they are the more likely they are nonsense rather than
something a programmer wrote by hand.

Training uses a set that is constructed from (1) a few thousand real
identifier strings taken from actual software, (2) a set of about 30,000
words taken from various contemporary text corpora, (3) a set of common stop
words, and (4) a few million strings created by randomly concatenating items
from 2-3 (but not the real identifiers, which are left as-is).  The current
stored results were produced after experimenting with 2-grams, 3-grams,
4-grams and 5-grams, and and different thresholds.  The best performance
achieved was reached with 4-grams, and that is the value stored in the
ngram_data.pklz pickle file in this directory.  The pickle file stores the
values computed by the function ngram_values(); each entry is a named tuple
of type NGramData and contains frequencies and IDF scores for each
n-gram.  (This can be done because IDF values can be precomputed based on a
training set, and do not reply on a particular string being tested during
classification -- the IDF values depend only on the frequency characteristics
of a particular training corpus.)

A final note: the code throughout this module uses only lower case letters in
input strings (by lower-casing the inputs).  I did actually try mixed-case
n-grams and input strings too, thinking this would be useful because our
inputs are often identifiers in camel case style, but then realized it
actually doesn't make sense for our purposes: given any identifier or text
string, there's no guarantee that the author will use camel case.  Often the
strings are simply all lower case anyway.

Training and testing
--------------------

The final performance of the nonsense detector is dependent on many things:
the characteristics of the training set, the length of the n-grams used, the
parameters in `string_score()`, and the threshold set in the function
`generate_nonsense_detector()`.

The comments in the file `training.py` provide information about how the
system is trained.  Basically, the process begins by generating a lot of
strings that are representative of program identifiers, then computing n-gram
frequency scores (IDF &ndash; inverse document frequency scores) and storing
them in a Python dictionary.  Then comes a period of adjusting the parameters
in the function `string_score()` and the thresholds in
`generate_nonsense_detector()`.  This can be done manually by scoring a lot
of both real and nonsense strings with the detector function created by
`generate_nonsense_detector()`, then guessing at likely values for the
thresholds and parameters, then re-scoring the example strings again, and
iterating this process until the detector function created by
`generate_nonsense_detector()` produces good results on real and random
strings.  A better method for finding optimal parameter values is to use a
multiobjectve optimization algorithm.  Nostril's parameter values were
initially derived manually and then fine-tuned using the NSGA-II
(Non-dominated Sorting Genetic Algorithm) routine in
Platypus (https://github.com/Project-Platypus/Platypus).

One of the characteristics of the training set is how the synthetic
identifier strings are generated.  The training set creation function,
`training_set()`, takes a parameter for the maximum number of words to
concatenate.  I experimented with 2-5, and found that a low number of 2
produced the best results (at least when combined with 4-grams).  The
current hypothesis for why a low, rather than high, number is better is that
concatenating real words at random produces character sequences that are,
well, random at the juncture points.  Since all the strings are scored for
n-grams, this increases n-gram IDF scores for some n-grams that are likely
to be random strings in real identifiers.  Now, this is not completely
undesirable: after all, programmers often combine acronyms, shorthand, and
unusual words when creating identifiers, and parts of those identifiers often
really do look like random character sequences.  So, there is a balancing act
here, in which we try to have some realistic randomness (but not too much)
in the training set.  The value of 2 for the parameter `max_concat_words`
in `training_set()` seems to produce the best results.

For the record, here is what I ultimately did to produce the final values in
`ngram_data.pklz`.  With the training set generation function,
`training_set()`, I experimented with setting `max_words` to 2-5, and
ultimately had best results with a value of 2.

    words = english_word_list()
    ids = identifiers_from_file('random-identifiers-from-github.txt')
    ts = training_set(words, ids, 3000000, 2)

The creation of the n-gram frequency table is as follows (here using
4-grams):

    freq = ngram_frequencies(ts, 4)

You can save the values of things like this:

    dataset_to_pickle('ngram_frequencies.pklz', freq)
    dataset_to_pickle('training/training_set.pklz', ts)

Potential improvements -- future work
-------------------------------------

Area #1: The optimization performed to arrive at the parameter values in
`generate_score_function()` and `generate_nonsense_detector()` did not vary
the size of n-grams or the training set characteristics.  It is possible that
including these features in the optimization would produce better-performing
results.  (The optimization would obviously be more time consuming, too.)  At
this point, rather than writing *more* code to explore more parameter values,
I chose to accept the current performance and stop further exploration.

Area #2: The n-gram approach here does not do anything special with the
beginnings and ends of strings.  By contrast, some authors report
improvements in their applications when they add phantom "start-of-string"
and "end-of-string" symbols to the strings before splitting them into
n-grams.  E.g., Freeman in "Using naive Bayes to detect spammy names in
social networks" (Proceedings of the 2013 ACM workshop on Artificial
Intelligence and Security) uses "^" to stand for the beginning and "$" to
stand for the end, so that "foo" is split into 3-grams as ['^fo', 'foo',
'oo$'].  In that work, it makes sense because they are matching human names,
and the beginnings and ends of names have some patterns that are different
from the insides of names.  This approach is not implemented in this module
(nonsense_detector) because it seems unlikely to have the same beneficial
effect.  From what we have seen in CASICS, program identifiers can start and
end with practically any character combination, and often they include
acronyms, which I suspect adds a lot more randomness than human names.
However, it has not been tested, and perhaps should be.

Authors
-------

Michael Hucka <mhucka@caltech.edu>

Copyright
---------

Copyright (c) 2017 by the California Institute of Technology.  This software
was developed as part of the CASICS project, the Comprehensive and Automated
Software Inventory Creation System.  For more, visit http://casics.org.

'''

from collections import defaultdict, Counter, namedtuple
from math import pow, log, ceil
import humanize
import os
import plac
import re
import string
import sys

if '__file__' in globals():
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../common'))
else:
    sys.path.append('../common')


# General n-gram functions.
# .............................................................................

def ngrams(string, n):
    '''Return all n-grams of length 'n' for the given 'string'.'''
    return [string[i : i + n] for i in range(len(string) - n + 1)]


def all_possible_ngrams(n):
    '''Recursively create all possible n-grams using lower case letters.'''
    all_letters = string.ascii_lowercase
    if n == 0:
        return []
    elif n == 1:
        return [letter for letter in all_letters]
    new_ngrams = []
    for letter in all_letters:
        for ngram in all_possible_ngrams(n - 1):
            new_ngrams.append(letter + ngram)
    return new_ngrams


# Functions to calculate scores for our modified TF-IDF.
# .............................................................................

def ngram_idf_value(total_num_strings, string_frequency,
                    total_frequency, max_frequency):
    '''Computes an inverse document frequency score.  In analogy to typical
    applications of IDF, a "document" in our case is a text string, and the
    "corpus" of documents is the set of all strings used for training.  This
    function takes the following arguments:
     * total_num_strings = total number of "documents" (= strings) in the corpus
     * string_frequency = document frequency (# strings in which n-gram appears)
     * total_frequency = total number of times n-gram appears across all docs
     * max_frequency = highest total_frequency value for any n-gram
    '''
    return log(total_num_strings/(1 + string_frequency), 2)
    # This next variant of the formula produces notably worse performance.
    # Leaving this here in case I'm tempted to try this again.  (Don't bother.)
    #    return log(max_frequency/(1 + string_frequency), 2)


def highest_idf(ngram_freq):
    '''Given a dictionary of n-gram score values for a corpus, returns the
    highest IDF value of any n-gram.
    '''
    return max(ngram_freq[n].idf for n in ngram_freq.keys())


def highest_total_frequency(ngram_freq):
    '''Given a dictionary of n-gram score values for a corpus, returns the
    highest total frequency of any n-gram.
    '''
    return max(ngram_freq[n].total_frequency for n in ngram_freq.keys())


def ngram_values(string_list, n, readjust_zero_scores=True):
    '''Given the corpus of strings in 'string_list', computes n-gram
    statistics across the corpus.  Returns the results as a dictionary
    containing all possible n-grams, where the dictionary keys are the
    n-grams as strings (e.g., 'aa', 'ab', 'ac', ...) and the dictionary
    values dictionary are the named tuple NGramData.  The numeric values
    inside the NGramData reflect the frequency statistics for that n-gram
    across the whole corpus.

    The optional argument 'readjust_zero_scores' governs what happens to the
    IDF values assigned to n-grams that do not appear in the corpus at all.
    If readjust_zero_scores = False, nothing is done, and the values are left
    at 0.  If readjust_zero_scores = True, the value is set equal to the
    highest IDF value found across the 'string_list' corpus.  (In our
    application, values of 0 in this situation are *not* desirable.  In IDF
    terms, a lower value indicates a more frequently-seen n-gram, whereas in
    our application, we look for uncommon n-grams and thus we want never-seen
    n-grams to have a *high* value.  This *could* be handled by detecting
    them when computing string scores, but that simply introduces needless
    repeated if-then tests in the step of computing scores for strings.  It
    is more efficient to store the desired value.  This is the reason the
    default is readjust_zero_scores = True.  Note that it is still possible
    to determine that a given n-gram does not appear in the corpus simply by
    looking at the string_frequency field of the NGramData tuple for that
    n-gram, so we do not really lose any information by doing this.)
    '''
    counts = defaultdict(int)
    occurrences = defaultdict(set)
    num_strings = 0
    for string in string_list:
        string = string.lower()
        num_strings += 1
        for ngram in ngrams(string, n):
            occurrences[ngram].add(string)
            counts[ngram] += 1
    # Set initial values for all n-grams.
    all_ngrams = defaultdict.fromkeys(all_possible_ngrams(n),
                                      NGramData(string_frequency=0,
                                                total_frequency=0,
                                                idf=0))
    # Set n-gram values based on occurrences in the corpus.
    max_frequency = max([count for ngram, count in counts.items()])
    for ngram, string_list in occurrences.items():
        string_freq = len(string_list)
        total_freq = counts[ngram]
        score = ngram_idf_value(num_strings, string_freq, total_freq, max_frequency)
        all_ngrams[ngram] = NGramData(string_frequency=string_freq,
                                      total_frequency=total_freq,
                                      idf=score)
    # Now that we've seen all n-grams actually present in the corpus, go back
    # and set those that have 0 values to a very high value (=> rare n-gram).
    if readjust_zero_scores:
        max_idf = ceil(highest_idf(all_ngrams))
        for ngram, value in all_ngrams.items():
            if value.idf == 0:
                # Can't set a value in an existing tuple; must regenerate tuple
                all_ngrams[ngram] = NGramData(string_frequency=0,
                                              total_frequency=0,
                                              idf=max_idf)
    return all_ngrams


def tfidf_score_function(ngram_freq, len_threshold=25, len_penalty_exp=1.365,
                         repetition_penalty_exp=1.159):
    '''Generate a function (as a closure) that computes a score for a given
    string.  This needs to be called to create the function like this:
        score_string = tfidf_score_function(...args...)
    The resulting scoring function can be called to score a string like this:
        score = score_string('yourstring')
    The formula implemented is as follows:

        S = a string to be scored (not given here, but to the function created)

        ngram_freq = table of NGramData named tuples
        ngram_length = the "n" in n-grams
        max_freq = max frequency of any n-gram
        num_ngrams = number of (any) n-grams of length n in S
        length_penalty = pow(max(0, num_ngrams - len_threshold), len_penalty_exp)
        ngram_score_sum = 0
        for every n-gram in S:
            c = count of times the n-gram appears in S
            idf = IDF score of n-gram from ngram_freq
            tf = 0.5 + 0.5*( c/max_freq )
            repetition_penalty = pow(c, repetition_penalty_exp)
            ngram_score_sum += (tf * idf * repetition_penalty)
        final score = (ngram_score_sum + length_penalty)/(1 + num_ngrams)

    The repetition_penalty is designed to penalize strings that contain a lot
    of repeats of the same n-gram.  Such repetition is a strong indicator of
    junk strings like "foofoofoofoofoo".  It works on the principle that for
    an exponent value y between 1 and 2, c^y is equal to the value of c for c
    = 1, a little bit more than c for c = 2, a little bit more still than c
    for c = 3, and so on; in other words, progressively increases the value
    for higher counts.  We do this because we can't directly penalize strings
    on the basis of length (see below).

    The division by num_ngrams in the final step is a scaling factor to deal
    with different string lengths.  The need for a scaling factor comes from
    the fact that very long identifiers can be real, and thus length by
    itself is not a good predictor of junk strings.  Without a length scaling
    factor, longer strings would end up with higher scores simply because
    we're adding up n-gram score values.

    Though it's true that string length is not a predictor of junk strings,
    it is true that extremely long strings are less likely to be real
    identifiers.  The addition of length_penalty in the formula above is used
    to penalize very long strings.  Even though long identifiers can be real,
    there comes a point where increasing length is more indicative of random
    strings.  Exploratory analysis suggests that this comes around 50-60
    characters.  The formula is designed to add nothing until the length
    exceeds this, and then to progressively increase in value as the length
    increases.

    Finally, note the implementation uses the number of n-grams in the string
    rather than the length of the string directly.  The number of n-grams is
    proportional to the length of the string, but getting the size of a
    dictionary is faster than taking the length of a string -- this approach
    is just an optimization.
    '''
    max_freq = highest_total_frequency(ngram_freq)
    ngram_length = len(next(iter(ngram_freq.keys())))
    len_threshold = int(len_threshold)
    def score_function(string):
        # Generate list of n-grams for the given string.
        string_ngrams = ngrams(string, ngram_length)
        # Count up occurrences of each n-gram in the string.
        ngram_counts = defaultdict(int)
        for ngram in string_ngrams:
            ngram_counts[ngram] += 1
        num_ngrams = len(string_ngrams)
        length_penalty = pow(max(0, num_ngrams - len_threshold), len_penalty_exp)
        score = sum(ngram_freq[n].idf * pow(c, repetition_penalty_exp) * (0.5 + 0.5*c/max_freq)
                    for n, c in ngram_counts.items()) + length_penalty
        return score/(1 + num_ngrams)
    return score_function


# Scoring and evaluating strings.
# .............................................................................

_delchars = str.maketrans('', '', string.punctuation + string.digits + ' ')
'''
List of characters to delete from input strings before computing scores.
'''

def generate_nonsense_detector(ngram_freq=None,
                               min_length=6, min_score=8.47, trace=False,
                               pickle_file='ngram_data.pklz',
                               score_len_threshold=25,
                               score_len_penalty_exp=0.9233,
                               score_rep_penalty_exp=0.9674):
    '''Returns (as a closure) a function that can take a single argument and
    return True if a given string is gibberish and False otherwise.  Usage:

       # Create the test function.
       is_nonsense = generate_nonsense_detector(ngram_freq)

       # Call the test function, for example in an if-statement:
       if is_nonsense('yourstring'):
           ... your code to do something here ...

    If not given a value for ngram_freq, it will look in the current
    directory for a pickled data file.  The name of the file is given by
    the argument 'pickle_file'.
    '''
    if not ngram_freq:
        file = full_path(pickle_file)
        if not os.path.exists(file):
            raise ValueError('Cannot find pickle file {}'.format(file))
        ngram_freq = dataset_from_pickle(file)
    string_score = tfidf_score_function(ngram_freq,
                                        len_threshold=score_len_threshold,
                                        len_penalty_exp=score_len_penalty_exp,
                                        repetition_penalty_exp=score_rep_penalty_exp)
    if trace:
        def nonsense_detector(string, show=trace):
            # Lower-case the string & remove non-letters before checking length.
            string = string.lower().translate(_delchars)
            if len(string) < min_length:
                raise ValueError('Too short to test')
            score = string_score(string)
            result = score > min_score
            if show:
                msg('"{}": {} (score {:.4f} threshold {:.4f})'
                    .format(string, 'y' if result else 'n', score, min_score))
            return result
    else:
        def nonsense_detector(string, show=trace):
            # Lower-case the string & remove non-letters before checking length.
            string = string.lower().translate(_delchars)
            if len(string) < min_length:
                raise ValueError('Too short to test')
            return string_score(string) > min_score
    return nonsense_detector


# Pickling utilities.
# .............................................................................
#
# Because of how Python pickles work, this code needs to stay here, rather
# than being put in a separate file/module.  If it's put in a separate file,
# you will get the obscure error
#    AttributeError: Can't get attribute 'NGramData' on <module '__main__'>
# when you try to read the pickle file.  The reason the error occurs is that
# a Python pickle does not store information about the data structure
# definition; it stores only its name.  That name is '__main__.NGramData',
# where '__main__' is the value of the module __name__ attribute.  If the
# pickle is read from another file, that will not be the value of __name__;
# the value of __name__ will be whatever that module's name is.  NGramData
# will not be defined in that module, and consequently, the pickle load will
# fail.

def dataset_from_pickle(file):
    '''Return the contents of the compressed pickle file in 'file'.  The
    pickle is assumed to contain only one data structure.
    '''
    import gzip, pickle
    try:
        from . import ng
        sys.modules['ngrams'] = ng
    except:
        pass
    with gzip.open(file, 'rb') as pickle_file:
        return pickle.load(pickle_file)


def dataset_to_pickle(file, data_set):
    '''Save the contents of 'data_set' to the compressed pickle file 'file'.
    The pickle is assumed to contain only one data structure.
    '''
    import gzip, pickle
    with gzip.open(file, 'wb') as pickle_file:
        pickle.dump(data_set, pickle_file)


# Miscellaneous general utilities.
# .............................................................................

def full_path(filename, subdir=None):
    '''Return a full path based on the current file or current working dir.
    'filename' is assumed to be a simple file name and not a path.  Optional
    'subdir' can be a subdirectory relative, to the current directory, where
    'filename' is found.
    '''
    if subdir and os.path.isabs(subdir):
        return os.path.join(subdir, filename)
    else:
        import inspect
        try:
            calling_file = inspect.getfile(sys._getframe(1))
            thisdir = os.path.dirname(os.path.realpath(calling_file))
        except:
            if '__file__' in globals():
                thisdir = os.path.dirname(os.path.realpath(__file__))
            else:
                thisdir = os.getcwd()
        if subdir:
            return os.path.join(os.path.join(thisdir, subdir), filename)
        else:
            return os.path.join(thisdir, filename)


def msg(text):
    '''Like the standard print(), but flushes the output immediately and
    colorizes the output by default. Flushing immediately is useful when
    piping the output of a script, because Python by default will buffer the
    output in that situation and this makes it very difficult to see what is
    happening in real time.
    '''
    print(text, flush=True)


# Testing utilities.
# .............................................................................

def tabulate_scores(string_list, ngram_freq, show=50, portion='all',
                    order='descending', precomputed=None, doreturn=False):
    from operator import itemgetter
    from tabulate import tabulate
    if precomputed:
        sorted_scores = sorted(precomputed, key=itemgetter(1),
                               reverse=not(order.startswith('ascend')))
    else:
        scores = []
        ngram_length = len(next(iter(ngram_freq.keys())))
        max_frequency = highest_total_frequency(ngram_freq)
        for string in string_list:
            score = string_score(string, ngram_freq, ngram_length, max_frequency)
            scores.append([string, score])
        sorted_scores = sorted(scores, key=itemgetter(1),
                               reverse=not(order.startswith('ascend')))
    if isinstance(show, int):
        if portion == 'all':
            show_scores = sorted_scores[0::int(len(sorted_scores)/show)]
        elif portion == 'top':
            show_scores = sorted_scores[:show]
        else:
            show_scores = sorted_scores[-show:]
    else:
        show_scores = [s for s in sorted_scores if s[0] == show]
    print('-'*70)
    if isinstance(show, int):
        print('Showing {} values sorted by {} column'.format(show, ordinal(1)))
    print(tabulate(show_scores, tablefmt=format, headers=['String', 'score ']))
    print('-'*70)
    if doreturn:
        return sorted_scores


def test_strings(input, nonsense_tester, min_length=6, sense='valid',
                 trace_scores=False, save_to=None):
    '''Test against a file or list of strings.  'nonsense_tester' is a
    function that should return True if a given string is nonsense.  'sense'
    indicates whether each input string should be considerd to be a valid
    string, or not.  If the input strings are valid, then
    nonsense_detector(...) should report False for each one; if the input
    strings are not valid, then nonsense_detector(...) should report True for
    each one.  Input strings that are shorter than 'min_length' are skipped.
    This function returns a tuple of totals and the time it took:
       (num_failures, num_successes, num_tested, num_skipped, elapsed_time)
    If the argument 'save_to' is not None, then it is assumed to be a filename
    and any and all stdout output will be redirected to the file.
    '''
    from time import time
    from contextlib import redirect_stdout

    def run_tests(trace_scores):
        failures = 0
        successes = 0
        skipped = 0
        count = 0
        start = time()
        for string in id_list:
            # Lower-case the string & remove non-letters before checking length.
            string = string.lower().translate(_delchars)
            if len(string) < min_length:
                skipped += 1
                continue
            count += 1
            is_junk = nonsense_tester(string, trace_scores)
            # Shortcut using the fact that True == 1 in numeric context.
            if sense == 'valid':
                failures += is_junk
                successes += not is_junk
            else:
                failures += not is_junk
                successes += is_junk
        elapsed_time = time() - start
        return (failures, successes, count, skipped, elapsed_time)

    def print_stats(failures, successes, count, skipped, elapsed_time):
        percent = 100*successes/(failures + successes)
        msg('{:.2f}% correct ({} tested in {:.2f}s, {} failures, {} successes, {} skipped)'
            .format(percent, humanize.intcomma(count), elapsed_time,
                    humanize.intcomma(failures), humanize.intcomma(successes),
                    humanize.intcomma(skipped)))

    if isinstance(input, list):
        id_list = input
    elif isinstance(input, str):
        # Assume the string is a file name
        file = os.path.join(os.getcwd(), input)
        with open(file, 'r') as f:
            id_list = f.read().splitlines()
    else:
        raise ValueError('First argument not understood: {}'.format(input))

    if save_to:
        with open(save_to, "w") as f:
            with redirect_stdout(f):
                (fails, successes, count, skipped, time) = run_tests(trace_scores=True)
        msg('-'*70)
        if trace_scores:
            print_stats(fails, successes, count, skipped, time)
        return (fails, successes, count, skipped, time)
    else:
        (fails, successes, count, skipped, time) = run_tests(trace_scores=trace_scores)
        if trace_scores:
            print_stats(fails, successes, count, skipped, time)
        return (fails, successes, count, skipped, time)


def test_labeled(input_file, nonsense_tester, min_length=6, trace_scores=False,
                 save_to=None):
    '''Test against a file containing labeled test cases.  'nonsense_tester'
    is a function that should return True if a given string is nonsense.
    Each line in the 'input_file' is assumed to contain two items separated
    by a comma: the letter 'y' or 'n', and then a string.  If an input string
    is labeled with 'y', it means it is a valid (not nonsense) string and
    nonsense_detector(...) should report False; if the input string labeled
    with 'n', it is not valid and nonsense_detector(...)  should report True.
    Input strings that are shorter than 'min_length' are skipped.
    This function returns a tuple of lists and totals and the time it took:
       (list_false_pos, list_false_neg, num_tested, num_skipped, elapsed_time)
    If the argument 'save_to' is not None, then it is assumed to be a
    filename and any and all stdout output will be redirected to the file.
    '''
    from time import time
    from contextlib import redirect_stdout

    def run_tests(filename, trace_scores):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:
            false_positives = []
            false_negatives = []
            skipped = 0
            count = 0
            start = time()
            lines = f.readlines()
            for line in lines:
                pieces = line.strip().split(',')
                is_real = (pieces[0] == 'y')
                string = pieces[1]
                if len(string) < min_length:
                    skipped += 1
                    continue
                count += 1
                if is_real:
                    if nonsense_tester(string, trace_scores):
                        false_positives.append(string)
                else:
                    if not nonsense_tester(string, trace_scores):
                        false_negatives.append(string)
            elapsed_time = time() - start
            if trace_scores:
                msg('{} cases tested in {:.2f}s, {} skipped -- {} false positives, {} false negatives'
                    .format(humanize.intcomma(count), elapsed_time,
                            humanize.intcomma(skipped),
                            humanize.intcomma(len(false_positives)),
                            humanize.intcomma(len(false_negatives))))
            return (false_positives, false_negatives, count, skipped, elapsed_time)

    if save_to:
        with open(save_to, "w") as f:
            with redirect_stdout(f):
                return run_tests(input_file, trace_scores=trace_scores)
    else:
        return run_tests(input_file, trace_scores=trace_scores)


# Module exports.
# .............................................................................

is_nonsense = generate_nonsense_detector()


# -----------------------------------------------------------------------------
# Saving for history

# This approach of using substring matches is much, much slower than
# using a hash table of all possible n-grams and testing membership.
#
# def num_substring_matches(substr, string):
#     # Implementation based on http://stackoverflow.com/a/6844623/743730
#     return sum(string[i:].startswith(substr) for i in range(len(string)))
#
# def string_score(string, ngram_freq):
#     # Given the ngram_values, calculate a score for the given string.
#     score = 0
#     for ngram, values in ngram_freq.items():
#         score += num_substring_matches(ngram, string) * values[2]
#     return score/len(string)

# Slower than version using sum() above
#
# def num_substring_matches(substr, string):
#     count = 0
#     for i in range(len(string)):
#         if string[i:].startswith(substr):
#             count += 1
#     return count


# def show_ngram_matches(string, ngram_freq):
#     # Lower-case the string and remove non-letter characters.
#     string = string.lower().translate(_delchars)
#     # Generate list of n-grams for the given string.
#     ngram_length = len(next(iter(ngram_freq.keys())))
#     string_ngrams = ngrams(string, ngram_length)
#     # Count up occurrences of each n-gram.
#     found = defaultdict(int)
#     for ngram in string_ngrams:
#         found[ngram] += 1
#     msg('{} unique n-grams'.format(len(found)))
#     max_tf = highest_total_frequency(ngram_freq)
#     for ng, count in found.items():
#         msg('{}: {} x {} (max {}) score = {}'
#             .format(ng, count, ngram_freq[ng].idf, max_tf,
#                     ngram_freq[ng].idf * pow(count, 1.195) * (0.5 + 0.5*count/ngram_freq[ng].max_frequency)))

#!/usr/bin/env python
# Code imported from
# https://dbaumgartel.wordpress.com/2014/04/10/an-elastic-mapreduce-streaming-example-with-python-and-ngrams-on-aws/

import sys
 
def CleanWord(aword):
    """
    Function input: A string which is meant to be
       interpreted as a single word.
    Output: a clean, lower-case version of the word
    """
    # Make Lower Case
    aword = aword.lower()
    # Remvoe special characters from word
    for character in '.,;:\'?':
        aword = aword.replace(character,'')
    # No empty words
    if len(aword)==0:
        return None
    # Restrict word to the standard english alphabet
    for character in aword:
        if character not in 'abcdefghijklmnopqrstuvwxyz':
            return None
    # return the word
    return aword
 
# Now we loop over lines in the system input
for line in sys.stdin:
    # Strip the line of whitespace and split into a list
    line = line.strip().split()
    # Use CleanWord function to clean up the word
    word = CleanWord(line[0])
 
    # If CleanWord didn't return a string, move on
    if word == None:
        continue
 
    # Get the year and the number of occurrences from
    # the ngram line
    year = int(line[1])
    occurrences = int(line[2])
 
    # Print the output: word, year, and number of occurrences
    print '%s\t%s\t%s' % (word, year,occurrences)

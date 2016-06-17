#!/usr/bin/env python
# code imported from
# https://dbaumgartel.wordpress.com/2014/04/10/an-elastic-mapreduce-streaming-example-with-python-and-ngrams-on-aws/

import sys
 
# current_word will be the word in each loop iteration
current_word = ''
# word_in_progress will be the word we have been working
# on for the last few iterations
word_in_progress = ''
 
# target_year_count is the number of word occurrences
# in the target year
target_year_count = 0
# prior_year_count is the number of word occurrenes
# in the years prior to the target year
prior_year_count = 0
 
# Define the target year, in our case 1999
target_year = 1999
 
# Loop over lines of input from STDIN
for line in sys.stdin:
 
    # Get the items in the line as a list
    line = line.strip().split('\t')
 
    # If for some reason there are not 3 items,
    # then move on to next line
    if len(line)!=3:
        continue
 
    # The line consists of a word, a year, and
    # a number of occurrences
    current_word, year, occurrences =  line
 
    # If we are on a new word, check the info of the last word
    # Print if it is a newly minted word, and zero our counters
    if current_word != word_in_progress:
        # Word exists in target year
        if target_year_count > 0:
            # Word doesn't exist in target year
            if prior_year_count ==0:
                # Print the cool new word and its occurrences
                print '%s\t%s' % (word_in_progress,target_year_count)
 
        # Zero our counters
        target_year_count = 0
        prior_year_count = 0
        word_in_progress = current_word
 
    # Get the year and occurences as integers
    # Continue if there is a problem
    try:
        year = int(year)
    except ValueError:
        continue
    try:
         occurrences = int(occurrences)
    except ValueError:
        continue
 
    # Update our variables
    if year == target_year:
        target_year_count += occurrences
    if year < target_year:
        prior_year_count += occurrences
 
# Since the loop is over, print the last word if applicable
if target_year_count > 0:
    # Word doesn't exist in target year
    if prior_year_count ==0:
        # Print the cool new word and its occurrences
        print '%s\t%s' % (word_in_progress,target_year_count)

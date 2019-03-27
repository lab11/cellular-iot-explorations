#! /usr/bin/env python3

import ast
import numpy as np
import scipy.stats as st
import sys

# get input file
if len(sys.argv) < 2:
    print("Error. Expected:\n\t./parse-results.py filename")
    sys.exit()
infilename = sys.argv[1]

# parse data file
post_results = {}
get_results = {}
with open(infilename, 'r') as infile:
    next_is_post = False
    next_is_get = False
    for line in infile:
        if line == 'POST results:\n':
            next_is_post = True
            continue
        if next_is_post and line[0] == '{':
            print("Found POST")
            next_is_post = False
            post_results = ast.literal_eval(line)

        if line == 'GET results:\n':
            next_is_get = True
            continue
        if next_is_get and line[0] == '{':
            print("Found GET")
            next_is_get = False
            get_results = ast.literal_eval(line)

# parse data
for name, result in (("POST", post_results), ("GET", get_results)):
    print("\n{} Results".format(name))
    for size in sorted(result.keys()):
        count_val = len(result[size])
        min_val = min(result[size])
        max_val = max(result[size])
        mean_val = np.mean(result[size])
        median_val = np.median(result[size])

        ci = st.t.interval(0.95, count_val-1, loc=mean_val, scale=st.sem(result[size]))
        ci_lower_val = ci[0]
        ci_upper_val = ci[1]

        print("\t{:5} Bytes - Count: {}\tMin: {:1.3f}\tMax: {:3.3f}\tMean: {:1.3f}\tMedian: {:1.3f}\tCI-: {:1.3f}\t CI+: {:1.3f}".format(size, count_val, min_val, max_val, mean_val, median_val, ci_lower_val, ci_upper_val))


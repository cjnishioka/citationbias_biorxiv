# -------------------------------------------
#
# Figure 1
#
# -------------------------------------------

import json
import pandas as pd
import os
import traceback
import gzip
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import sys
from statistics import mean
import math
from operator import truediv

pd.options.display.float_format = '{:,.2f}'.format

#=========================#
# settings
#=========================#

# input file
file_input = 'data/biorxiv_metadata-oc.jsonl.gz'

# latest month
latest_month = datetime.strptime('2021-06', '%Y-%m')

# number of months for counting the number of citations after preprint publication
max_months = 24

# ISSNL of target journal (if 'all', all journals are considered)
target_journal = 'all'

# conditions for the number of months from publication of preprint to publication of publisher version (if no criteria, set 'na')
diff_month_preprint_publisher_min = 0
diff_month_preprint_publisher_max = 'na'

# metric of the number of citations
metric = 'ln' # arithmetic mean of the log-transformed number of citation after addition of 1
# metric = 'arithmetic-mean' # arithmetic mean

#=========================#

#=========================#
# count the number of citations
#=========================#

# lists that record the number of citations, preprints, and publisher versions per the number of months since preprint publication
num_citations_preprint = [0] * (max_months + 1)
num_citations_published = [0] * (max_months + 1)
num_citations_preprint_ln = [0] * (max_months + 1)
num_citations_published_ln = [0] * (max_months + 1)
num_articles_preprint = [0] * (max_months + 1)
num_articles_published = [0] * (max_months + 1)

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

c = 0
num_articles = 0

with gzip.open(file_input,'rt') as f:
    for line in f:
        if c % 10000 == 0:
            print(c, flush=True)
        c += 1

        json_obj = json.loads(line.strip())

        biorxiv_month = datetime.strptime(json_obj['month'], '%Y-%m')

        # DOI of publisher version
        # if no DOI, filter out the record from the analysis
        published_doi = json_obj.get('published_doi', None)
        if published_doi == None:
            continue

        # publication of month of the publisher version
        # if no publication month, filter out the record from the analysis
        try:
            published_month = datetime.strptime(json_obj['published_month'], '%Y-%m')
        except:
            continue

        # if the record has a citation period whose length is less than $max_months$-month, filter out the record from the analysis
        if diff_month(latest_month, biorxiv_month) < max_months:
            continue

        # if the conditions for the number of months from publication of preprint to publication of publisher version are not met, filter out the record from the analysis
        if diff_month_preprint_publisher_min != 'na':
            if diff_month(published_month, biorxiv_month) < diff_month_preprint_publisher_min:
                continue
        if diff_month_preprint_publisher_max != 'na':
            if diff_month(published_month, biorxiv_month) > diff_month_preprint_publisher_max:
                continue

        # author affiliation
        authors = json_obj['author']['authors']
        if len(authors) == 0:
            continue

        #### preprints and publisher versions that reach this point are analyzed  ####

        num_articles += 1

        # count the number of preprints and publisher versions per the number of months since preprint publication
        available_months = diff_month(latest_month, biorxiv_month)
        for i in range(0, diff_month(published_month, biorxiv_month)):
            if i > max_months:
                break
            num_articles_preprint[i] += 1
        for i in range(diff_month(published_month, biorxiv_month), available_months + 1):
            if i > max_months:
                break
            num_articles_published[i] += 1

        # count the number of citations per the number of months since preprint publication
        citations = json_obj['oc']
        month_citations = {}
        for citation in citations:
            # get publication month of a citing entity
            # if no publication month, filter out the citation from the analysis
            try:
                if len(citation['creation_month']) == 4:
                    citation_month = datetime.strptime(citation['creation_month'] + '-01', '%Y-%m')
                else:
                    citation_month = datetime.strptime(citation['creation_month'], '%Y-%m')
            except:
                continue

            # count the number of months from publication of preprint to citation
            # if the number of months is smaller than 0 or exceeds $max_month$ months, filter out the citation
            months = diff_month(citation_month, biorxiv_month)
            if months < 0 or months > max_months:
                continue
            month_citations[citation_month] = month_citations.get(citation_month, 0) + 1

            # judge whether a citation is to preprint or publisher version
            if citation['cited_doi'].startswith('10.1101') == False:
                num_citations_published[months] += 1
            else:
                num_citations_preprint[months] += 1


        for key in month_citations.keys():
            if diff_month(key, published_month) > 0:
                num_citations_published[diff_month(key, biorxiv_month)] += month_citations[key]
                num_citations_published_ln[diff_month(key, biorxiv_month)] += math.log(month_citations[key] + 1)
            else:
                num_citations_preprint[diff_month(key, biorxiv_month)] += month_citations[key]
                num_citations_preprint_ln[diff_month(key, biorxiv_month)] += math.log(month_citations[key] + 1)


if metric == 'ln':
    num_citations_preprint_final = list(map(truediv, num_citations_preprint_ln, num_articles_preprint))
    num_citations_published_final = list(map(truediv, num_citations_published_ln, num_articles_published))
elif metric == 'arithmetic-mean':
    num_citations_preprint_final = list(map(truediv, num_citations_preprint, num_articles_preprint))
    num_citations_published_final = list(map(truediv, num_citations_published, num_articles_published))

print(num_articles)

#=========================#
# generate a figure
#=========================#

l = list(range(0, max_months + 1))

fig = plt.figure()

ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(2, 1, 2)

ax1.minorticks_on()
ax1.grid(which='major', axis='x')
ax1.grid(which='major', axis='y')
ax1.grid(which='minor', axis='y', linestyle=':')

ax2.set_axisbelow(True)
ax2.grid(which='both', axis='x')
ax2.grid(which='both', axis='y')

ax1.set_xlim(-1.3925000000000003, 25.392500000000002)
ax1.plot(l, num_citations_preprint_final, marker="x", markersize=2, linewidth=1, color='r', label='preprint')
ax1.plot(l, num_citations_published_final, marker="o", markersize=2, linewidth=1, color='b', label='publisher version')
ax1.tick_params(labelbottom=False, bottom=False)

ax2.bar(l, num_articles_preprint, 0.35, color='r', label='preprint')
ax2.bar(l, num_articles_published, 0.35, color='b', bottom=num_articles_preprint, label='publisher version')

ax1.set_ylabel('number of citations\n(log-transformed\nafter addition of 1)')
ax2.set_ylabel('number of articles')
ax2.set_xlabel('months after preprint publication')

ax1.legend()
ax2.legend()
fig.tight_layout()
fig.savefig('figure/time_articles_citations.png', dpi=300)

#=========================#

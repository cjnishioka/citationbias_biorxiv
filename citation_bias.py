# -------------------------------------------
#
# depict Lorenz curve and calculate Gini coefficients
#
# -------------------------------------------

# modules
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

#=========================#
# setting
#=========================#

plt.rcParams['font.size'] = 18
pd.options.display.float_format = '{:,.2f}'.format


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def gini(x):
    # https://stackoverflow.com/questions/39512260/calculating-gini-coefficient-in-python-numpy
    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad / np.mean(x)
    # Gini coefficient
    g = 0.5 * rmad
    return g


def citation_ineq(file_input, latest_month, max_months, target_author, affiliation_level, target_journal, diff_month_preprint_publisher_min, diff_month_preprint_publisher_max, num_articles_min, none_citation_included, unknown_excluded, metric, fig=True):

    print(latest_month, max_months, target_author, affiliation_level, target_journal, diff_month_preprint_publisher_min, diff_month_preprint_publisher_max, num_articles_min, none_citation_included, unknown_excluded, metric, fig)

    #=========================#

    if affiliation_level == 'institution':
        ror_field = 'ror_name'
    elif affiliation_level == 'country':
        ror_field = 'ror_country'

    #=========================#

    # プレプリントと出版者版の被引用数を記録するデータフレーム
    citations_affiliations = pd.DataFrame(0, index=[], columns=[
                                          'preprint', 'published', 'num_articles', 'preprint_ln', 'published_ln'], dtype='float')

    c = 0
    with gzip.open(file_input, 'rt') as f:
        for line in f:

            json_obj = json.loads(line.strip())

            biorxiv_month = datetime.strptime(json_obj['month'], '%Y-%m')

            # DOI of publisher version
            # if no DOI, filter out the record from the analysis
            published_doi = json_obj.get('published_doi', None)
            if published_doi == None:
                continue

            # target journal
            if target_journal != 'all':
                if json_obj.get('published_journalissnl', '') != target_journal:
                    continue

            # publication of month of the publisher version
            # if no publication month, filter out the record from the analysis
            try:
                published_month = datetime.strptime(
                    json_obj['published_month'], '%Y-%m')
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
            if json_obj['author']['estimate'] == True and target_author != 'all':
                continue
            affiliations = {}
            author_identified = False
            for author in authors:
                if target_author == 'first':
                    if author['author_order'] == 1:
                        author_identified = True
                        if len(author['affiliations']) > 0:
                            for a in author['affiliations']:
                                try:
                                    affiliations[a['ror'][ror_field]] = affiliations.get(a['ror'][ror_field], 0) + (1 / len(author['affiliations']))
                                except:
                                    affiliations['unknown'] = affiliations.get('unknown', 0) + (1 / len(author['affiliations']))
                        else:
                            affiliations['unknown'] = affiliations.get('unknown', 0) + 1
                        break
                elif target_author == 'corresp':
                    if author['corresp'] == True:
                        author_identified = True
                        if len(author['affiliations']) > 0:
                            for a in author['affiliations']:
                                try:
                                    affiliations[a['ror'][ror_field]] = affiliations.get(a['ror'][ror_field], 0) + (1 / len(author['affiliations']))
                                except:
                                    affiliations['unknown'] = affiliations.get('unknown', 0) + (1 / len(author['affiliations']))
                        else:
                            affiliations['unknown'] = affiliations.get('unknown', 0) + 1
                        break
                elif target_author == 'last':
                    if author['author_order'] == len(authors):
                        author_identified = True
                        if len(author['affiliations']) > 0:
                            for a in author['affiliations']:
                                try:
                                    affiliations[a['ror'][ror_field]] = affiliations.get(a['ror'][ror_field], 0) + (1 / len(author['affiliations']))
                                except:
                                    affiliations['unknown'] = affiliations.get('unknown', 0) + (1 / len(author['affiliations']))
                        else:
                            affiliations['unknown'] = affiliations.get('unknown', 0) + 1
                        break
                elif target_author == 'all':
                    if len(author['affiliations']) > 0:
                        for a in author['affiliations']:
                            try:
                                affiliations[a['ror'][ror_field]] = affiliations.get(a['ror'][ror_field], 0) + (1 / len(authors) / len(author['affiliations']))
                            except:
                                affiliations['unknown'] = affiliations.get('unknown', 0) + (1 / len(authors) / len(author['affiliations']))
                    else:
                        affiliations['unknown'] = affiliations.get('unknown', 0) + (1 / len(authors))

            if (target_author != 'all') and (author_identified == False):
                continue

            if (none_citation_included == False) and (len(json_obj['oc']) == 0):
                continue

            #### preprints and publisher versions that reach this point are analyzed  ####

            # count the number of articles
            for affiliation in affiliations.keys():
                if (affiliation in citations_affiliations.index.tolist()) == False:
                    citations_affiliations.loc[affiliation] = [
                        0] * len(citations_affiliations.columns)
                citations_affiliations.at[affiliation,
                                          'num_articles'] += affiliations[affiliation]

            # count the number of citations
            citations = json_obj['oc']
            citation_preprint = 0
            citation_published = 0
            for citation in citations:
                try:
                    if len(citation['creation_month']) == 4:
                        citation_month = datetime.strptime(
                            citation['creation_month'] + '-01', '%Y-%m')
                    else:
                        citation_month = datetime.strptime(
                            citation['creation_month'], '%Y-%m')
                except:
                    continue

                months = diff_month(citation_month, biorxiv_month)
                if months < 0 or months > max_months:
                    continue

                if citation['cited_doi'].startswith('10.1101'):
                    citation_preprint += 1
                else:
                    citation_published += 1

            for affiliation in affiliations.keys():
                citations_affiliations.at[affiliation, 'published'] += (
                    citation_published * affiliations[affiliation])
                citations_affiliations.at[affiliation,
                                          'preprint'] += (citation_preprint * affiliations[affiliation])
                citations_affiliations.at[affiliation, 'published_ln'] += math.log(
                    citation_published + 1) * affiliations[affiliation]
                citations_affiliations.at[affiliation, 'preprint_ln'] += math.log(
                    citation_preprint + 1) * affiliations[affiliation]

                # citations_affiliations.at[affiliation, 'published'] += (citation_published / len(affiliations))
                # citations_affiliations.at[affiliation, 'preprint'] += (citation_preprint / len(affiliations))
                # citations_affiliations.at[affiliation, 'published_ln'] += math.log(citation_published + 1) / len(affiliations)
                # citations_affiliations.at[affiliation, 'preprint_ln'] += math.log(citation_preprint + 1) / len(affiliations)

    # if unknown_excluded is set as True, remove articles and citations whose affiliation is unknown
    if unknown_excluded == True and 'unknown' in list(citations_affiliations.index.values):
        citations_affiliations = citations_affiliations.drop(index='unknown')

    # filter out affiliations whose number of articles is less than num_articles_min
    citations_affiliations = citations_affiliations[
        citations_affiliations['num_articles'] >= num_articles_min]

    if metric == 'ln':
        citations_affiliations['published_metric'] = citations_affiliations['published_ln'] / \
            citations_affiliations['num_articles']
        citations_affiliations['preprint_metric'] = citations_affiliations['preprint_ln'] / \
            citations_affiliations['num_articles']
    elif metric == 'arithmetic-mean':
        citations_affiliations['published_metric'] = citations_affiliations['published'] / \
            citations_affiliations['num_articles']
        citations_affiliations['preprint_metric'] = citations_affiliations['preprint'] / \
            citations_affiliations['num_articles']
    elif metric == 'total':
        citations_affiliations['published_metric'] = citations_affiliations['published']
        citations_affiliations['preprint_metric'] = citations_affiliations['preprint']

    #####################
    # depict Lorenz curve
    #####################
    citations_preprints = citations_affiliations['preprint_metric'].tolist()
    citations_preprints.sort()
    citations_preprints_cum = [citations_preprints[0]]
    for i in range(1, len(citations_preprints)):
        citations_preprints_cum.append(
            citations_preprints_cum[i - 1] + citations_preprints[i])
    citations_preprints_cum.insert(0, 0)

    citations_published = citations_affiliations['published_metric'].tolist()
    citations_published.sort()
    citations_published_cum = [citations_published[0]]
    for i in range(1, len(citations_published)):
        citations_published_cum.append(
            citations_published_cum[i - 1] + citations_published[i])
    citations_published_cum.insert(0, 0)

    if fig == True:

        l = [0]
        for i in range(1, len(citations_affiliations) + 1):
            l.append(i / len(citations_affiliations))

        fig, ax = plt.subplots()

        plt.tight_layout()

        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.plot(l, np.array(citations_preprints_cum) /
                 citations_preprints_cum[-1], marker="x", markersize=0, linewidth=1, color='r', label='preprint')
        plt.plot(l, np.array(citations_published_cum) /
                 citations_published_cum[-1], marker="o", markersize=0, linewidth=1, color='b', label='publisher version')
        plt.grid(which='both', axis='y')
        ax.legend()

        filename = target_author + '_' + affiliation_level + '_' + target_journal + '_' + str(diff_month_preprint_publisher_min) + '-' + str(
            diff_month_preprint_publisher_max) + '_' + str(num_articles_min) + '_' + str(unknown_excluded).lower() + '_' + str(none_citation_included).lower() + '_' + metric
        fig.savefig('figure/lorenz_' + filename + '.png', dpi=300)
    #####################

    # return Gini coefficients, number of articles (i.e., pairs of preprints and publisher versions), and number of affiliations
    return gini(np.array(citations_preprints)), gini(np.array(citations_published)), citations_affiliations['num_articles'].sum(), len(citations_affiliations)


##############################

# file input
file_input = 'data/biorxiv_metadata-oc.jsonl.gz'

# latest month
latest_month = datetime.strptime('2021-06', '%Y-%m')


##########
# Section 3.2
##########
print('============')
print('Section 3.2')
print('============')

fw = open('result/gini_institution_target-authors.tsv', 'w')
for at in ['first', 'last', 'corresp', 'all']:
    gini_preprint, gini_publisher, num_articles, num_affiliations = citation_ineq(file_input=file_input, latest_month=latest_month, max_months=24, target_author=at, affiliation_level='institution',
                                                                                  target_journal='all', diff_month_preprint_publisher_min=0, diff_month_preprint_publisher_max='na', num_articles_min=5, none_citation_included=True, unknown_excluded=True, metric='ln')
    fw.write(at + '\t' + str(gini_preprint) + '\t' + str(gini_publisher) +
             '\t' + str(num_articles) + '\t' + str(num_affiliations) + '\n')
fw.close()

fw = open('result/gini_country_target-authors.tsv', 'w')
for at in ['first', 'last', 'corresp', 'all']:
    gini_preprint, gini_publisher, num_articles, num_affiliations = citation_ineq(file_input=file_input, latest_month=latest_month, max_months=24, target_author=at, affiliation_level='country',
                                                                                  target_journal='all', diff_month_preprint_publisher_min=0, diff_month_preprint_publisher_max='na', num_articles_min=10, none_citation_included=True, unknown_excluded=True, metric='ln')
    fw.write(at + '\t' + str(gini_preprint) + '\t' + str(gini_publisher) +
             '\t' + str(num_articles) + '\t' + str(num_affiliations) + '\n')
fw.close()

##########
# Section 3.3
##########
print('============')
print('Section 3.3')
print('============')

fw = open('result/gini_institution_all_3.tsv', 'w')
for i in range(0, 24):
    gini_preprint, gini_publisher, num_articles, num_affiliations = citation_ineq(file_input=file_input, latest_month=latest_month, max_months=24, target_author='all', affiliation_level='institution',
                                                                                  target_journal='all', diff_month_preprint_publisher_min=i, diff_month_preprint_publisher_max=i, num_articles_min=3, none_citation_included=True, unknown_excluded=True, metric='ln', fig=False)
    fw.write(str(i) + '\t' + str(gini_preprint) + '\t' + str(gini_publisher) +
             '\t' + str(num_articles) + '\t' + str(num_affiliations) + '\n')
fw.close()

fw = open('result/gini_country_all_5.tsv', 'w')
for i in range(0, 24):
    gini_preprint, gini_publisher, num_articles, num_affiliations = citation_ineq(file_input=file_input, latest_month=latest_month, max_months=24, target_author='all', affiliation_level='country',
                                                                                  target_journal='all', diff_month_preprint_publisher_min=i, diff_month_preprint_publisher_max=i, num_articles_min=5, none_citation_included=True, unknown_excluded=True, metric='ln', fig=False)
    fw.write(str(i) + '\t' + str(gini_preprint) + '\t' + str(gini_publisher) +
             '\t' + str(num_articles) + '\t' + str(num_affiliations) + '\n')
fw.close()

##########
# Section 3.4
##########
print('============')
print('Section 3.4')
print('============')

# 1932-6203 PLoS ONE
# 2045-2322 Scientific Reports
# 0305-1048 Nucleic acids research
# 0006-3495 Biophysical journal
# 1061-4036 Nature Genetics
# 0028-0836 Nature
# 0036-8075 Science

fw = open('result/gini_journals.tsv', 'w')
for tj in ['1932-6203', '2045-2322', '0305-1048', '0006-3495', '1061-4036', '0028-0836', '0036-8075']:
    for al in ['institution', 'country']:
        for at in ['all']:
            gini_preprint, gini_publisher, num_articles, num_affiliations = citation_ineq(file_input=file_input, latest_month=latest_month, max_months=24, target_author=at, affiliation_level=al,
                                                                                          target_journal=tj, diff_month_preprint_publisher_min=0, diff_month_preprint_publisher_max='na', num_articles_min=0, none_citation_included=True, unknown_excluded=True, metric='ln', fig=False)
            fw.write(tj + '\t' + al + '\t' + at + '\t' + str(gini_preprint) + '\t' + str(
                gini_publisher) + '\t' + str(num_articles) + '\t' + str(num_affiliations) + '\n')
fw.close()

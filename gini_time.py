# -------------------------------------------
#
# Figure 3 and Figure 4
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


df = pd.read_csv('result/gini_institution_all_3.tsv', sep='\t', names=('months', 'gini_preprint', 'gini_publisher', 'num_articles', 'num_affiliations'))
# df = pd.read_csv('result/gini_country_all_5.tsv', sep='\t', names=('months', 'gini_preprint', 'gini_publisher', 'num_articles', 'num_affiliations'))

fig = plt.figure()
fig.set_size_inches(5, 5.5)

ax1 = fig.add_subplot(3, 1, 1)
ax2 = fig.add_subplot(3, 1, 2)
ax3 = fig.add_subplot(3, 1, 3)

major_ticks = np.arange(0, 21, 5)
minor_ticks = np.arange(0, 21, 1)

ax1.set_xticks(major_ticks)
ax1.set_xticks(minor_ticks, minor=True)

ax1.grid(which='major', alpha=0.5)
ax1.grid(which='minor', axis='x', alpha=0.2, linestyle=':')
ax1.grid(which='minor', axis='y', alpha=0.2, linestyle=':')

ax2.set_axisbelow(True)
ax2.set_xticks(major_ticks)
ax2.set_xticks(minor_ticks, minor=True)
ax2.grid(which='major', axis='x', alpha=0.5)
ax2.grid(which='minor', axis='x', alpha=0.2, linestyle=':')
ax2.grid(which='major', axis='y', alpha=0.5)

ax3.set_axisbelow(True)
ax3.set_xticks(major_ticks)
ax3.set_xticks(minor_ticks, minor=True)
ax3.grid(which='major', axis='x', alpha=0.5)
ax3.grid(which='minor', axis='x', alpha=0.2, linestyle=':')
ax3.grid(which='major', axis='y', alpha=0.5)

ax1.plot(df['months'][0:19], df['gini_preprint'][0:19], marker="x", markersize=2, linewidth=1, color='r', label='preprint')
ax1.plot(df['months'][0:19], df['gini_publisher'][0:19], marker="o", markersize=2, linewidth=1, color='b', label='publisher version')
ax1.set_xlim(-1.1000, 19.202499999999997)
ax1.tick_params(labelbottom=False, bottom=False)

ax2.set_xticks(major_ticks)
ax2.set_xticks(minor_ticks, minor=True)
ax2.bar(df['months'][0:19], df['num_articles'][0:19], 0.25, color='green', label='number of articles')
ax2.tick_params(labelbottom=False, bottom=False)

ax3.set_xticks(major_ticks)
ax3.set_xticks(minor_ticks, minor=True)
ax3.bar(df['months'][0:19], df['num_affiliations'][0:19], 0.25, color='gray', label='number of affiliations')

ax1.set_ylabel('Gini coefficient')
ax2.set_ylabel('number of articles')
ax3.set_ylabel('number of affiliations')
ax3.set_xlabel('months from publication of a preprint to its publisher version')

ax1.legend()
fig.tight_layout()

fig.savefig('figure/gini_institution_all_3.png', dpi=300)
# fig.savefig('figure/gini_country_all_5.png', dpi=300)

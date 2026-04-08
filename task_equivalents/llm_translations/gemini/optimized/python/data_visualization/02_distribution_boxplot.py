import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

college = pd.read_csv('data/csv/College.csv', index_col=0)

college['Elite'] = np.where(college['Top10perc'] > 50, 'Yes', 'No')

# First plot: Boxplot (equivalent to plot(factor, numeric) in R)
fig1, ax1 = plt.subplots()
college.boxplot(column='Outstate', by='Elite', ax=ax1, grid=False)
fig1.suptitle('')
ax1.set_title('')
ax1.set_xlabel('Elite')
ax1.set_ylabel('Out-of-state tuition')

# Second plot: 2x2 grid of histograms
fig2, axes = plt.subplots(2, 2, figsize=(10, 8))

axes[0, 0].hist(college['Apps'], bins=50, edgecolor='black')
axes[0, 0].set_xlabel('new applications')

axes[0, 1].hist(college['Enroll'], bins=45, edgecolor='black')
axes[0, 1].set_xlabel('new enrollment')

axes[1, 0].hist(college['Expend'], bins=30, edgecolor='black')
axes[1, 0].set_xlabel('Instructional expenditure per student')

axes[1, 1].hist(college['Outstate'], edgecolor='black')
axes[1, 1].set_xlabel('Out-of-state tuition')

plt.tight_layout()
plt.show()
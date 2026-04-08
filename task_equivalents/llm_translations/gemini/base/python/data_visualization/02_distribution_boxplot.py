import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

college = pd.read_csv('data/csv/College.csv', index_col=0)

college['Elite'] = np.where(college['Top10perc'] > 50, 'Yes', 'No')
college['Elite'] = college['Elite'].astype('category')

# R's plot(factor, numeric) creates a boxplot
plt.figure()
college.boxplot(column='Outstate', by='Elite', grid=False)
plt.title('')
plt.suptitle('')
plt.xlabel('Elite')
plt.ylabel('Out-of-state tuition')

# dev.new() and par(mfrow=c(2,2)) equivalent
fig, axes = plt.subplots(2, 2, figsize=(10, 8))

axes[0, 0].hist(college['Apps'], bins=50, edgecolor='black', facecolor='none')
axes[0, 0].set_xlabel('new applications')

axes[0, 1].hist(college['Enroll'], bins=45, edgecolor='black', facecolor='none')
axes[0, 1].set_xlabel('new enrollment')

axes[1, 0].hist(college['Expend'], bins=30, edgecolor='black', facecolor='none')
axes[1, 0].set_xlabel('Instructional expenditure per student')

axes[1, 1].hist(college['Outstate'], edgecolor='black', facecolor='none')
axes[1, 1].set_xlabel('Out-of-state tuition')

plt.tight_layout()
plt.show()
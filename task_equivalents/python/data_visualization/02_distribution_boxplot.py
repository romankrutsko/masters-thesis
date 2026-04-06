# Extracted from Ch02.py (Q8 visualization)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

college = pd.read_csv('C:\\Users\\Carol\\Desktop\\college.csv')
school_name = college.iloc[:, 0]
college = college.rename(index=lambda i: school_name[i])
college.drop(college.columns[[0]], axis=1, inplace=True)
college['Private'] = college.Private.astype('category')

college['Elite'] = np.where(college['Top10perc'] > 50, 'Yes', 'No')
college['Elite'] = college.Elite.astype('category')

sns.boxplot(x='Elite', y='Outstate', data=college)

fig = plt.figure()
fig.add_subplot(2, 2, 1)
plt.hist(college['Apps'], 50)
plt.xlabel('new applications')
fig.add_subplot(2, 2, 2)
plt.hist(college['Enroll'], 45)
plt.xlabel('new enrollment')
fig.add_subplot(2, 2, 3)
plt.hist(college['Expend'], 30)
plt.xlabel('Instructional expenditure per student')
fig.add_subplot(2, 2, 4)
plt.hist(college['Outstate'])
plt.xlabel('Out-of-state tuition')

import pandas as pd
import matplotlib.pyplot as plt

college = pd.read_csv('data/csv/College.csv', header=0)
college.index = college.iloc[:, 0]
college = college.iloc[:, 1:]

Elite = pd.Series('No', index=college.index)
Elite[college['Top10perc'] > 50] = 'Yes'
Elite = Elite.astype('category')
college['Elite'] = Elite

plt.figure()
plt.scatter(college['Elite'].cat.codes, college['Outstate'])
plt.xticks([0, 1], college['Elite'].cat.categories)
plt.xlabel('Elite')
plt.ylabel('Out-of-state tuition')
plt.show()

plt.figure()
fig, axes = plt.subplots(2, 2)
axes[0, 0].hist(college['Apps'], bins=50)
axes[0, 0].set_xlabel('new applications')
axes[0, 0].set_title('')

axes[0, 1].hist(college['Enroll'], bins=45)
axes[0, 1].set_xlabel('new enrollment')
axes[0, 1].set_title('')

axes[1, 0].hist(college['Expend'], bins=30)
axes[1, 0].set_xlabel('Instructional expenditure per student')
axes[1, 0].set_title('')

axes[1, 1].hist(college['Outstate'])
axes[1, 1].set_xlabel('Out-of-state tuition')
axes[1, 1].set_title('')

plt.tight_layout()
plt.show()
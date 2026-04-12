import pandas as pd

college = pd.read_csv('data/csv/College.csv')
college.set_index(college.columns[0], inplace=True)
college.drop(college.columns[0], axis=1, inplace=True)

elite = ['No' for _ in range(len(college))]
for i, row in college.iterrows():
    if row['Top10perc'] > 50:
        elite[i] = 'Yes'
elite = pd.Series(elite, name='Elite')
college = college.assign(Elite=elite)

import matplotlib.pyplot as plt

plt.scatter(college['Elite'], college['Outstate'])
plt.xlabel('Elite')
plt.ylabel('Out-of-state tuition')
plt.show()

fig, axes = plt.subplots(2, 2)
axes[0, 0].hist(college['Apps'], bins=50)
axes[0, 0].set_xlabel('new applications')
axes[0, 1].hist(college['Enroll'], bins=45)
axes[0, 1].set_xlabel('new enrollment')
axes[1, 0].hist(college['Expend'], bins=30)
axes[1, 0].set_xlabel('Instructional expenditure per student')
axes[1, 1].hist(college['Outstate'])
axes[1, 1].set_xlabel('Out-of-state tuition')
plt.tight_layout()
plt.show()

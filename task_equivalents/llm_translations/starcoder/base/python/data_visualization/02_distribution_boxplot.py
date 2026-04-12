import pandas as pd
import matplotlib.pyplot as plt

college = pd.read_csv('data/csv/College.csv', index_col=0)

college['Elite'] = 'No'
college.loc[college['Top10perc'] > 50, 'Elite'] = 'Yes'
college['Elite'] = college['Elite'].astype('category')

fig, ax = plt.subplots()
ax.scatter(college['Elite'], college['Outstate'])
ax.set_xlabel('Elite')
ax.set_ylabel('Out-of-state tuition')
plt.show()

fig, axes = plt.subplots(2, 2)
axes[0, 0].hist(college['Apps'], bins=50)
axes[0, 0].set_xlabel('New applications')
axes[0, 1].hist(college['Enroll'], bins=45)
axes[0, 1].set_xlabel('New enrollment')
axes[1, 0].hist(college['Expend'], bins=30)
axes[1, 0].set_xlabel('Instructional expenditure per student')
axes[1, 1].hist(college['Outstate'])
axes[1, 1].set_xlabel('Out-of-state tuition')
plt.show()
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
college = pd.read_csv('data/csv/College.csv', index_col=0)

# Create the Elite column
college['Elite'] = (college['Top10perc'] > 50).map({True: 'Yes', False: 'No'}).astype('category')

# Plot Elite vs Outstate
plt.figure(figsize=(8, 6))
plt.scatter(college['Elite'], college['Outstate'])
plt.xlabel('Elite')
plt.ylabel('Out-of-state tuition')
plt.show()

# Plot histograms
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
axs[0, 0].hist(college['Apps'], bins=50)
axs[0, 0].set_xlabel('new applications')
axs[0, 1].hist(college['Enroll'], bins=45)
axs[0, 1].set_xlabel('new enrollment')
axs[1, 0].hist(college['Expend'], bins=30)
axs[1, 0].set_xlabel('Instructional expenditure per student')
axs[1, 1].hist(college['Outstate'], bins='auto')
axs[1, 1].set_xlabel('Out-of-state tuition')
plt.tight_layout()
plt.show()
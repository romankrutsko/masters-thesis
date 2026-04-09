import pandas as pd
import numpy as np

# Load the data
college = pd.read_csv('data/csv/College.csv', index_col=0)

# Create a new column 'Private01' and drop 'Private'
college['Private01'] = (college['Private'] == 'Yes').astype(int)
college = college.drop('Private', axis=1)

# Split data into X and Y
X = college.drop('Apps', axis=1).apply(pd.to_numeric)
Y = college['Apps']

# Split data into training and test sets
np.random.seed(1)
idx = np.random.permutation(len(college))
train_idx, test_idx = idx[:len(college)//2], idx[len(college)//2:]
xtrain, xtest = X.iloc[train_idx], X.iloc[test_idx]
ytrain, ytest = Y.iloc[train_idx], Y.iloc[test_idx]
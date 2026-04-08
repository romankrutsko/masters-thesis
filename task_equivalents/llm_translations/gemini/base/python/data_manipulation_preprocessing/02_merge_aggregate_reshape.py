import pandas as pd
import numpy as np

College = pd.read_csv('data/csv/College.csv', index_col=0)

College['Private01'] = (College['Private'] == 'Yes').astype(int)
College = College.drop(columns=['Private'])

X = College.drop(columns=['Apps']).apply(pd.to_numeric)
Y = College['Apps']

np.random.seed(1)
train = np.random.choice(len(College), len(College) // 2, replace=False)
test = np.setdiff1d(np.arange(len(College)), train)

xtrain = X.iloc[train]
xtest  = X.iloc[test]
ytrain = Y.iloc[train]
ytest  = Y.iloc[test]
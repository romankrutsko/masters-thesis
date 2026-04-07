import pandas as pd
import numpy as np

College = pd.read_csv('data/csv/College.csv', header=0)
College.index = College.iloc[:, 0]
College = College.iloc[:, 1:]

College['Private01'] = (College['Private'] == 'Yes').astype(int)
College = College.drop(columns=['Private'])

X = College.drop(columns=['Apps']).apply(pd.to_numeric)
Y = College['Apps']

np.random.seed(1)
train = np.random.choice(College.index, size=len(College) // 2, replace=False)
test = College.index.difference(train)

xtrain = X.loc[train]
xtest = X.loc[test]
ytrain = Y.loc[train]
ytest = Y.loc[test]
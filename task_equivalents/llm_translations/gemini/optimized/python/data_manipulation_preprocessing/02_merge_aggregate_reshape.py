import pandas as pd
from sklearn.model_selection import train_test_split

College = pd.read_csv('data/csv/College.csv', index_col=0)

College['Private01'] = (College['Private'] == 'Yes').astype(int)
College = College.drop(columns=['Private'])

X = College.drop(columns=['Apps']).apply(pd.to_numeric)
Y = College['Apps']

xtrain, xtest, ytrain, ytest = train_test_split(X, Y, test_size=0.5, random_state=1)
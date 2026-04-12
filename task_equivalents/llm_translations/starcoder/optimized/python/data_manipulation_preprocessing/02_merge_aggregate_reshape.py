import pandas as pd

College = pd.read_csv('data/csv/College.csv', header=True)
College.set_index(College.columns[0], inplace=True)
College['Private01'] = (College['Private'] == 'Yes').astype(int)
College.drop('Private', axis=1, inplace=True)
X = College.loc[:, College.columns != 'Apps'].apply(pd.to_numeric)
Y = College['Apps']
train = College.sample(frac=0.5, random_state=1).index
test = [i for i in College.index if i not in train]
xtrain = X.loc[train]
xtest = X.loc[test]
ytrain = Y.loc[train]
ytest = Y.loc[test]

# Extracted from Ch08.py (Q8 decision tree workflow + CV)

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error

Carseats = pd.read_csv('C:\\Users\\Carol\\Desktop\\Carseats.csv')
Carseats['Urban']     = Carseats.Urban.map({'No':0, 'Yes':1})
Carseats['US']        = Carseats.US.map({'No':0, 'Yes':1})
Carseats['ShelveLoc'] = pd.factorize(Carseats.ShelveLoc)[0]
Carseats              = Carseats.drop('Unnamed: 0', axis=1)

x = Carseats.drop(['Sales'], axis=1)
y = Carseats['Sales']
xtrain, xtest, ytrain, ytest = train_test_split(x, y, train_size=0.5, random_state=1)

tree_carseats = DecisionTreeRegressor()
tree_carseats.fit(xtrain, ytrain)
ypred = tree_carseats.predict(xtest)
mean_squared_error(ytest, ypred)

depth = []
for i in range(1,11):
    cv_tree = DecisionTreeRegressor(max_depth=i)
    scores  = cross_val_score(estimator=cv_tree, X=xtrain, y=ytrain, cv=10)
    depth.append(scores.mean())
plt.plot(range(1,11), depth)

pruned_tree_carseats = DecisionTreeRegressor(max_depth=depth.index(max(depth))+1)
pruned_tree_carseats.fit(xtrain, ytrain)
ypred = pruned_tree_carseats.predict(xtest)
mean_squared_error(ytest, ypred)

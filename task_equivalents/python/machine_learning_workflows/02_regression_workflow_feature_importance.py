# Extracted from Ch08.py (Q10 boosting/lasso workflow)

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LassoCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

Hitters = pd.read_csv('C:\\Users\\Carol\\Desktop\\Hitters.csv').drop('Unnamed: 0', axis=1).dropna()
Hitters['League'] = Hitters.League.map({'A':0, 'N':1})
Hitters['NewLeague'] = Hitters.NewLeague.map({'A':0, 'N':1})
Hitters['Division'] = Hitters.Division.map({'E':0, 'W':1})
Hitters['logSal'] = np.log(Hitters.Salary)

x = Hitters.drop(['Salary', 'logSal'], axis=1)
y = Hitters['logSal']
xtrain, xtest, ytrain, ytest = train_test_split(x, y, train_size=200, random_state=1)

lambda_grid = np.linspace(0.001, 0.201, 20)
train_mse = np.zeros(20)
for i in range(20):
    boost = GradientBoostingRegressor(n_estimators=1000, learning_rate=lambda_grid[i], random_state=2)
    boost.fit(xtrain, ytrain)
    train_mse[i] = mean_squared_error(ytrain, boost.predict(xtrain))

lasso = LassoCV(cv=10, normalize=True).fit(xtrain, ytrain)
lasso_mse = mean_squared_error(ytest, lasso.predict(xtest))

best_lambda = lambda_grid[train_mse.argmin()]
best_boost = GradientBoostingRegressor(n_estimators=1000, learning_rate=best_lambda, random_state=2)
best_boost.fit(xtrain, ytrain)

feature_importance = pd.Series(best_boost.feature_importances_ * 100, index=xtrain.columns).sort_values(ascending=False)
print(feature_importance)

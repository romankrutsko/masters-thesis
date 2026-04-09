import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LassoCV

# Load data
Hitters = pd.read_csv('data/csv/Hitters.csv', index_col=0)

# Data preprocessing
Hitters = Hitters.dropna()
drop_cols = ['Player', 'Name']
Hitters = Hitters.drop(drop_cols, axis=1, errors='ignore')
Hitters['League'] = np.where(Hitters['League'] == 'A', 0, 1)
Hitters['NewLeague'] = np.where(Hitters['NewLeague'] == 'A', 0, 1)
Hitters['Division'] = np.where(Hitters['Division'] == 'E', 0, 1)
Hitters['logSal'] = np.log(Hitters['Salary'])

X = Hitters.drop(['Salary', 'logSal'], axis=1)
y = Hitters['logSal']

# Split data into training and testing sets
np.random.seed(1)
train_idx, test_idx = train_test_split(range(len(X)), test_size=len(X)-200, random_state=1)
xtrain, xtest = X.iloc[train_idx], X.iloc[test_idx]
ytrain, ytest = y.iloc[train_idx], y.iloc[test_idx]

# Gradient Boosting
train_mse = np.zeros(20)
lambda_grid = np.linspace(0.001, 0.201, 20)
for i, lam in enumerate(lambda_grid):
    boost_hit = GradientBoostingRegressor(n_estimators=1000, learning_rate=lam, loss='squared_error')
    boost_hit.fit(xtrain, ytrain)
    boost_pred = boost_hit.predict(xtrain)
    train_mse[i] = mean_squared_error(ytrain, boost_pred)

# Lasso regression
lasso_cv = LassoCV(cv=10, max_iter=10000)
lasso_cv.fit(xtrain, ytrain)
lasso_pred = lasso_cv.predict(xtest)
lasso_mse = mean_squared_error(ytest, lasso_pred)

# Best lambda for Gradient Boosting
best_lambda = lambda_grid[np.argmin(train_mse)]
best_boost_hit = GradientBoostingRegressor(n_estimators=1000, learning_rate=best_lambda, loss='squared_error')
best_boost_hit.fit(xtrain, ytrain)

# Feature importance
feature_importances = best_boost_hit.feature_importances_
print('Feature Importances:')
for feature, importance in zip(xtrain.columns, feature_importances):
    print(f'{feature}: {importance:.3f}')
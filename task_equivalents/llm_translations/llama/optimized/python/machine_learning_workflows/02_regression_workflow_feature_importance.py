import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from glmnet import ElasticNet

# Load data
Hitters = pd.read_csv('data/csv/Hitters.csv', index_col=0)

# Preprocess data
Hitters = Hitters.dropna()
drop_cols = ['Player', 'Name']
drop_cols = [col for col in drop_cols if col in Hitters.columns]
Hitters = Hitters.drop(drop_cols, axis=1)
Hitters['League'] = (Hitters['League'] == 'N').astype(int)
Hitters['NewLeague'] = (Hitters['NewLeague'] == 'N').astype(int)
Hitters['Division'] = (Hitters['Division'] == 'W').astype(int)
Hitters['logSal'] = np.log(Hitters['Salary'])

# Split data into features and target
x = Hitters.drop(['Salary', 'logSal'], axis=1)
y = Hitters['logSal']

# Split data into training and test sets
np.random.seed(1)
train_idx, test_idx = train_test_split(range(len(x)), test_size=len(x)-200, random_state=1)
xtrain, xtest = x.iloc[train_idx], x.iloc[test_idx]
ytrain, ytest = y.iloc[train_idx], y.iloc[test_idx]

# Gradient Boosting
lambda_grid = np.linspace(0.001, 0.201, 20)
train_mse = np.zeros(20)
for i, lam in enumerate(lambda_grid):
    boost_hit = GradientBoostingRegressor(loss='squared_error', n_estimators=1000, learning_rate=lam, verbose=0)
    boost_hit.fit(xtrain, ytrain)
    boost_pred = boost_hit.predict(xtrain)
    train_mse[i] = mean_squared_error(ytrain, boost_pred)

# Lasso Regression
cv_out = ElasticNet(alpha=1, n_splits=10, random_state=1)
cv_out.fit(xtrain, ytrain)
best_lam = cv_out.lambda_best_
lasso_pred = cv_out.predict(xtest, s=best_lam)
lasso_mse = mean_squared_error(ytest, lasso_pred)

# Best Gradient Boosting Model
best_lambda = lambda_grid[np.argmin(train_mse)]
best_boost_hit = GradientBoostingRegressor(loss='squared_error', n_estimators=1000, learning_rate=best_lambda, verbose=0)
best_boost_hit.fit(xtrain, ytrain)

# Feature Importances
feature_importances = best_boost_hit.feature_importances_
print(pd.DataFrame({'Feature': xtrain.columns, 'Importance': feature_importances}).sort_values('Importance', ascending=False))

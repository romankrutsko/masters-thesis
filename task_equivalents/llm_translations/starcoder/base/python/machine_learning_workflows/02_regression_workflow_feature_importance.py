import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV, Lasso
Hitters = pd.read_csv('data/csv/Hitters.csv', header=0, index_col=0)
Hitters = Hitters.dropna()
Hitters = Hitters.drop(['Player', 'Name'], axis=1)
Hitters['League'] = (Hitters['League'] == 'A').astype(int)
Hitters['NewLeague'] = (Hitters['NewLeague'] == 'A').astype(int)
Hitters['Division'] = (Hitters['Division'] == 'E').astype(int)
Hitters['logSal'] = np.log(Hitters['Salary'])
x = Hitters.drop(['Salary', 'logSal'], axis=1)
y = Hitters['logSal']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=1)
train_mse = []
lambda_grid = np.linspace(0.001, 0.201, 20)
for lambda_val in lambda_grid:
    boost_hit = GradientBoostingRegressor(n_estimators=1000, learning_rate=lambda_val, random_state=1)
    boost_hit.fit(x_train, y_train)
    boost_pred = boost_hit.predict(x_train)
    train_mse.append(mean_squared_error(y_train, boost_pred))
lasso_cv = LassoCV(alphas=lambda_grid, cv=10, random_state=1)
lasso_cv.fit(x_train, y_train)
best_lambda = lasso_cv.alpha_
lasso = Lasso(alpha=best_lambda, random_state=1)
lasso.fit(x_train, y_train)
lasso_pred = lasso.predict(x_test)
lasso_mse = mean_squared_error(y_test, lasso_pred)
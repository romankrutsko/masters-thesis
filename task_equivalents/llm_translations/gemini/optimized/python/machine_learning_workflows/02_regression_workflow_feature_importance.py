import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

Hitters = pd.read_csv('data/csv/Hitters.csv', index_col=0)
Hitters = Hitters.dropna()

drop_cols = [col for col in ['rownames', 'Player', 'Name'] if col in Hitters.columns]
if drop_cols:
    Hitters = Hitters.drop(columns=drop_cols)

Hitters['League'] = np.where(Hitters['League'] == 'A', 0, 1)
Hitters['NewLeague'] = np.where(Hitters['NewLeague'] == 'A', 0, 1)
Hitters['Division'] = np.where(Hitters['Division'] == 'E', 0, 1)
Hitters['logSal'] = np.log(Hitters['Salary'])

x = Hitters.drop(columns=['Salary', 'logSal'])
y = Hitters['logSal']

xtrain, xtest, ytrain, ytest = train_test_split(x, y, train_size=200, random_state=1)

train_mse = np.zeros(20)
lambda_grid = np.linspace(0.001, 0.201, 20)

for i, lr in enumerate(lambda_grid):
    boost_hit = GradientBoostingRegressor(loss='squared_error', n_estimators=1000, learning_rate=lr, random_state=1)
    boost_hit.fit(xtrain, ytrain)
    boost_pred = boost_hit.predict(xtrain)
    train_mse[i] = mean_squared_error(ytrain, boost_pred)

cv_out = make_pipeline(StandardScaler(), LassoCV(cv=10, random_state=1, max_iter=10000))
cv_out.fit(xtrain, ytrain)
lasso_pred = cv_out.predict(xtest)
lasso_mse = mean_squared_error(ytest, lasso_pred)

best_lambda = lambda_grid[np.argmin(train_mse)]
best_boost_hit = GradientBoostingRegressor(loss='squared_error', n_estimators=1000, learning_rate=best_lambda, random_state=1)
best_boost_hit.fit(xtrain, ytrain)

summary = pd.DataFrame({
    'var': xtrain.columns,
    'rel.inf': best_boost_hit.feature_importances_ * 100
}).sort_values(by='rel.inf', ascending=False)
print(summary)
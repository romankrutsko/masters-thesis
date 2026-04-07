import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV

Hitters = pd.read_csv('data/csv/Hitters.csv', header=0, index_col=0)

Hitters = Hitters.dropna()
drop_cols = [col for col in ['rownames', 'Player', 'Name'] if col in Hitters.columns]
Hitters = Hitters.drop(columns=drop_cols)
Hitters['League'] = np.where(Hitters['League'] == 'A', 0, 1)
Hitters['NewLeague'] = np.where(Hitters['NewLeague'] == 'A', 0, 1)
Hitters['Division'] = np.where(Hitters['Division'] == 'E', 0, 1)
Hitters['logSal'] = np.log(Hitters['Salary'])

x = Hitters.drop(columns=['Salary', 'logSal'])
y = Hitters['logSal']

np.random.seed(1)
train = np.random.choice(np.arange(len(x)), size=200, replace=False)
test = np.setdiff1d(np.arange(len(x)), train)
xtrain = x.iloc[train]
xtest = x.iloc[test]
ytrain = y.iloc[train]
ytest = y.iloc[test]

train_mse = np.zeros(20)
lambda_grid = np.linspace(0.001, 0.201, 20)

for i, lam in enumerate(lambda_grid):
    boost_hit = GradientBoostingRegressor(
        n_estimators=1000,
        learning_rate=lam,
        random_state=1
    )
    boost_hit.fit(xtrain, ytrain)
    boost_pred = boost_hit.predict(xtrain)
    train_mse[i] = np.mean((boost_pred - ytrain) ** 2)

cv_out = LassoCV(cv=10, random_state=1)
cv_out.fit(xtrain.to_numpy(), ytrain.to_numpy())
bestlam = cv_out.alpha_
lasso_pred = cv_out.predict(xtest.to_numpy())
lasso_mse = np.mean((lasso_pred - ytest.to_numpy()) ** 2)

best_lambda = lambda_grid[np.argmin(train_mse)]
best_boost_hit = GradientBoostingRegressor(
    n_estimators=1000,
    learning_rate=best_lambda,
    random_state=1
)
best_boost_hit.fit(xtrain, ytrain)

feature_importance = pd.Series(
    best_boost_hit.feature_importances_,
    index=xtrain.columns
).sort_values(ascending=False)
print(feature_importance)
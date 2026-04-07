import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_squared_error

hitters = pd.read_csv("data/csv/Hitters.csv", index_col=0).dropna()

drop_cols = [col for col in ["rownames", "Player", "Name"] if col in hitters.columns]
hitters = hitters.drop(columns=drop_cols)

hitters["League"] = (hitters["League"] != "A").astype(int)
hitters["NewLeague"] = (hitters["NewLeague"] != "A").astype(int)
hitters["Division"] = (hitters["Division"] != "E").astype(int)
hitters["logSal"] = np.log(hitters["Salary"])

x = hitters.drop(columns=["Salary", "logSal"])
y = hitters["logSal"]

rng = np.random.RandomState(1)
train = rng.choice(len(x), size=200, replace=False)
test = np.setdiff1d(np.arange(len(x)), train)

xtrain = x.iloc[train]
xtest = x.iloc[test]
ytrain = y.iloc[train]
ytest = y.iloc[test]

train_mse = np.empty(20)
lambda_grid = np.linspace(0.001, 0.201, 20)

for i, lam in enumerate(lambda_grid):
    boost_hit = GradientBoostingRegressor(
        loss="squared_error",
        n_estimators=1000,
        learning_rate=lam,
        random_state=1,
    )
    boost_hit.fit(xtrain, ytrain)
    boost_pred = boost_hit.predict(xtrain)
    train_mse[i] = mean_squared_error(ytrain, boost_pred)

cv_out = LassoCV(cv=10, random_state=1).fit(xtrain.to_numpy(), ytrain.to_numpy())
bestlam = cv_out.alpha_
lasso_pred = cv_out.predict(xtest.to_numpy())
lasso_mse = mean_squared_error(ytest, lasso_pred)

best_lambda = lambda_grid[np.argmin(train_mse)]
best_boost_hit = GradientBoostingRegressor(
    loss="squared_error",
    n_estimators=1000,
    learning_rate=best_lambda,
    random_state=1,
)
best_boost_hit.fit(xtrain, ytrain)

summary = pd.DataFrame(
    {
        "var": xtrain.columns,
        "rel.inf": 100 * best_boost_hit.feature_importances_ / best_boost_hit.feature_importances_.sum(),
    }
).sort_values("rel.inf", ascending=False)

print(summary)
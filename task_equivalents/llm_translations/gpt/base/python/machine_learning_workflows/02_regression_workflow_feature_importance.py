import numpy as np
import pandas as pd
from patsy import dmatrices, dmatrix
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor

Hitters = pd.read_csv("data/csv/Hitters.csv", header=0, index_col=0)

char_cols = Hitters.select_dtypes(include=["object"]).columns
for col in char_cols:
    Hitters[col] = Hitters[col].astype("category")

Hitters = Hitters.dropna().copy()
Hitters["logSal"] = np.log(Hitters["Salary"])

np.random.seed(1)
train = np.random.choice(Hitters.index, size=200, replace=False)
hit_test = Hitters.loc[~Hitters.index.isin(train), "logSal"]

j = 0
train_mse = np.zeros(20)
for i in np.arange(0.001, 0.201, 0.01):
    boost_hit = GradientBoostingRegressor(
        n_estimators=1000,
        learning_rate=i,
        random_state=1
    )
    X_train_boost = dmatrix("~ . - Salary - logSal", data=Hitters.loc[train], return_type="dataframe")
    y_train_boost = Hitters.loc[train, "logSal"]
    boost_hit.fit(X_train_boost, y_train_boost)
    boost_pred = boost_hit.predict(X_train_boost)
    train_mse[j] = mean_squared_error(y_train_boost, boost_pred)
    j += 1

x_train = dmatrix("~ . - Salary - logSal", data=Hitters.loc[train], return_type="dataframe")
y_train = Hitters.loc[train, "logSal"]
x_test = dmatrix("~ . - Salary - logSal", data=Hitters.loc[~Hitters.index.isin(train)], return_type="dataframe")

cv_out = LassoCV(cv=10, random_state=1, max_iter=10000)
cv_out.fit(x_train, y_train)
bestlam = cv_out.alpha_
lasso_pred = cv_out.predict(x_test)
lasso_mse = mean_squared_error(hit_test, lasso_pred)

best_boost_hit = GradientBoostingRegressor(
    n_estimators=1000,
    learning_rate=0.011,
    random_state=1
)
best_boost_hit.fit(X_train_boost, y_train_boost)

feature_importance = pd.Series(
    best_boost_hit.feature_importances_,
    index=X_train_boost.columns
).sort_values(ascending=False)
print(feature_importance)
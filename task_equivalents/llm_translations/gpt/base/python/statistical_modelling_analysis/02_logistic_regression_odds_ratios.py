import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

Weekly = pd.read_csv("data/csv/Weekly.csv", header=0, index_col=0)
Weekly["Direction"] = Weekly["Direction"].astype("category")

glm1_fit = smf.glm(
    "Direction ~ Lag1 + Lag2 + Lag3 + Lag4 + Lag5 + Volume",
    data=Weekly,
    family=smf.families.Binomial()
).fit()
print(glm1_fit.summary())

n = Weekly.shape[0]
glm1_prob = glm1_fit.predict(Weekly)
glm1_pred = np.full(n, "Down", dtype=object)
glm1_pred[glm1_prob > 0.5] = "Up"

print(pd.crosstab(glm1_pred, Weekly["Direction"]))
print(np.mean(glm1_pred == Weekly["Direction"]))
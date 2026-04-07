import pandas as pd
import statsmodels.api as sm

weekly = pd.read_csv("data/csv/Weekly.csv", index_col=0)

x01 = weekly.iloc[:, 2:8].copy()
y01 = (weekly["Direction"] == "Up").astype(int)

x01 = sm.add_constant(x01)
glm0_fit = sm.GLM(y01, x01, family=sm.families.Binomial()).fit()
print(glm0_fit.summary())

prob = glm0_fit.predict(x01)
pred = (prob > 0.5).astype(int)
print(pd.crosstab(y01, pred, rownames=["Actual"], colnames=["Predicted"]))
print((pred == y01).mean())
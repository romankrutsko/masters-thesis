import pandas as pd
import statsmodels.api as sm

Weekly = pd.read_csv('data/csv/Weekly.csv', header=0, index_col=0)

x01 = Weekly.iloc[:, 2:8]
y01 = (Weekly['Direction'] == 'Up').astype(int)

x01_with_const = sm.add_constant(x01)
glm0_fit = sm.GLM(y01, x01_with_const, family=sm.families.Binomial()).fit()
print(glm0_fit.summary())

prob = glm0_fit.predict(x01_with_const)
pred = (prob > 0.5).astype(int)
print(pd.crosstab(y01, pred, rownames=['Actual'], colnames=['Predicted']))
print((pred == y01).mean())
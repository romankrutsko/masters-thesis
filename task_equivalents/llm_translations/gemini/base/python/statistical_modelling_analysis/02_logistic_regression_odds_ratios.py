import pandas as pd
import numpy as np
import statsmodels.api as sm

Weekly = pd.read_csv('data/csv/Weekly.csv', index_col=0)

x01 = Weekly.iloc[:, 2:8]
y01 = np.where(Weekly['Direction'] == 'Up', 1, 0)

X = sm.add_constant(x01)
glm0_fit = sm.Logit(y01, X).fit(disp=False)
print(glm0_fit.summary())

prob = glm0_fit.predict(X)
pred = np.where(prob > 0.5, 1, 0)

print(pd.crosstab(y01, pred, rownames=['Actual'], colnames=['Predicted']))
print(np.mean(pred == y01))
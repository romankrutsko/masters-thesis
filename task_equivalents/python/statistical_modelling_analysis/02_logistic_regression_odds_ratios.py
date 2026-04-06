# Extracted from Ch04.py (Q10 logistic regression)

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import confusion_matrix

Weekly = pd.read_csv('data/csv/Weekly.csv')

x01 = sm.add_constant(Weekly.iloc[:, 2:8])
y01 = np.where(Weekly['Direction'] == 'Up', 1, 0)

glm0_fit = sm.Logit(y01, x01).fit()
print(glm0_fit.summary())

prob = glm0_fit.predict(x01)
pred = np.where(prob > 0.5, 1, 0)
print(confusion_matrix(y01, pred))
print((pred == y01).mean())

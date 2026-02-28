# Extracted from Ch04.py (Q10 logistic regression)

import numpy as np
import pandas as pd
import statsmodels.api as sm

Weekly = pd.read_csv('C:\\Users\\Carol\\Desktop\\Weekly.csv')

x01 = sm.add_constant(Weekly.iloc[:, 2:8])
y01 = np.where(Weekly['Direction']=='Up', 1, 0)

glm0 = sm.Logit(y01, x01)
print(glm0.fit().summary())

# Extracted from Ch03.py (Q8 linear regression + inference)

import numpy as np
import pandas as pd
import statsmodels.api as sm

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

n = len(Auto['mpg'])
X = np.reshape(Auto['horsepower'], (n, 1))
Y = np.reshape(Auto['mpg'], (n, 1))

X = sm.add_constant(X)
model1_fit = sm.OLS(Y, X).fit()
print(model1_fit.summary())

xnew = np.array([[1., 98.]])
pred = model1_fit.get_prediction(xnew).summary_frame(alpha=0.05)
print(pred[['mean', 'mean_ci_lower', 'mean_ci_upper']])
print(pred[['mean', 'obs_ci_lower', 'obs_ci_upper']])

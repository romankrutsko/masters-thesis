# Extracted from Ch03.py (Q8 linear regression + inference)

import numpy as np
import pandas as pd
import statsmodels.api as sm

Auto = pd.read_csv('C:\\Users\\Carol\\Desktop\\Auto.csv', na_values='?')
Auto = Auto.dropna()

n = len(Auto['mpg'])
X = np.reshape(Auto['horsepower'], (n,1))
Y = np.reshape(Auto['mpg'], (n,1))

X          = sm.add_constant(X)
model1     = sm.OLS(Y, X)
model1_fit = model1.fit()
print(model1_fit.summary())

xnew = np.array([[1., 98.]])
ynew = model1_fit.get_prediction(xnew)
print(ynew.summary_frame(alpha=0.05))

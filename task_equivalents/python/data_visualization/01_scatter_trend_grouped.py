# Extracted from Ch03.py (Q8 visualization)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

n = len(Auto['mpg'])
X = np.reshape(Auto['horsepower'], (n, 1))
Y = np.reshape(Auto['mpg'], (n, 1))
X = sm.add_constant(X)
model1_fit = sm.OLS(Y, X).fit()

a = model1_fit.params[0]
b = model1_fit.params[1]
yfit = [a + b * xi for xi in X[:, 1]]

plt.scatter(X[:, 1], Y)
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.plot(X[:, 1], yfit, 'red')

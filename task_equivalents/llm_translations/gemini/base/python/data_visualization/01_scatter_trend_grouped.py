import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()

n = len(auto)
X_col = auto['horsepower'].to_numpy().reshape(-1, 1)
Y = auto['mpg'].to_numpy().reshape(-1, 1)
X = np.column_stack((np.ones(n), X_col))

model1 = sm.OLS(Y, X).fit()

a = model1.params[0]
b = model1.params[1]
yfit = a + b * X[:, 1]

plt.scatter(X[:, 1], Y, facecolors='none', edgecolors='k')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.plot(X[:, 1], yfit, color='red')
plt.show()
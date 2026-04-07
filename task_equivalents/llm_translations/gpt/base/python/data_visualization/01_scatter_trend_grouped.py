import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

auto = pd.read_csv('data/csv/Auto.csv', header=0, na_values='?')
auto = auto.dropna()

n = len(auto)
X = auto[['horsepower']].to_numpy()
Y = auto[['mpg']].to_numpy()
X_with_intercept = np.c_[np.ones(n), X]

model1 = LinearRegression()
model1.fit(X, Y)

a = model1.intercept_[0]
b = model1.coef_[0, 0]
yfit = a + b * X[:, 0]

plt.scatter(X[:, 0], Y[:, 0])
plt.plot(X[:, 0], yfit, color='red')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.show()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()

X = auto['horsepower'].values
Y = auto['mpg'].values

b, a = np.polyfit(X, Y, 1)
yfit = a + b * X

plt.scatter(X, Y)
plt.plot(X, yfit, color='red')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.show()
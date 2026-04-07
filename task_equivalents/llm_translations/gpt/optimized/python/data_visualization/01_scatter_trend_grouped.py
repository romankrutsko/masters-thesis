import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

auto = pd.read_csv("data/csv/Auto.csv", na_values="?").dropna()

n = len(auto)
X = auto["horsepower"].to_numpy().reshape(n, 1)
Y = auto["mpg"].to_numpy().reshape(n, 1)
X = np.c_[np.ones(n), X]

b = np.linalg.lstsq(X, Y, rcond=None)[0]
a = b[0, 0]
b = b[1, 0]
yfit = a + b * X[:, 1]

plt.plot(X[:, 1], Y[:, 0], "o")
plt.xlabel("horsepower")
plt.ylabel("mpg")
plt.plot(X[:, 1], yfit, color="red")
plt.show()
Here's the translated code from R to Python:

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()

X = auto['horsepower'].values.reshape(-1, 1)
Y = auto['mpg'].values.reshape(-1, 1)

model = LinearRegression()
model.fit(X, Y)

a = model.intercept_
b = model.coef_[0]
yfit = a + b * X

import matplotlib.pyplot as plt

plt.scatter(X, Y, c='blue', label='Original Data')
plt.plot(X, yfit, c='red', label='Fitted Line')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.legend()
plt.show()
```
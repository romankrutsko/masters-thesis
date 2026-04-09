import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Load the data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

# Prepare the data
X = auto[['horsepower']].values
Y = auto['mpg'].values.reshape(-1, 1)

# Add a constant (intercept) to the independent value
X_const = np.hstack((np.ones((X.shape[0], 1)), X))

# Perform simple linear regression
model = LinearRegression(fit_intercept=False)
model.fit(X_const, Y)

a, b = model.coef_[0]
yfit = model.predict(X_const)

# Plot the data and the regression line
plt.scatter(X, Y)
plt.plot(X, yfit, color='red')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.show()
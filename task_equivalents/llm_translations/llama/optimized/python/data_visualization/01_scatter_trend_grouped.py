import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Load data and remove rows with missing values
auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

# Prepare data for linear regression
X = auto[['horsepower']]
Y = auto['mpg']

# Perform linear regression
model = LinearRegression(fit_intercept=True)
model.fit(X, Y)

# Predict Y values
yfit = model.predict(X)

# Plot data and regression line
plt.scatter(X, Y, label='Data')
plt.plot(X, yfit, color='red', label='Regression Line')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.legend()
plt.show()
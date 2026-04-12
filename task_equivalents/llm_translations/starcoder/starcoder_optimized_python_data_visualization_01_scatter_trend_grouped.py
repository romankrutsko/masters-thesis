Here is the Python code that performs the same tasks as the given R code:

```python
import pandas as pd
auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()
n = len(auto)
X = auto['horsepower'].to_numpy().reshape((-1, 1))
Y = auto['mpg'].to_numpy().reshape((-1, 1))
X = np.column_stack((np.ones(n), X))
model1 = LinearRegression().fit(X[:, 1].reshape((-1, 1)), Y)
a = model1.intercept_[0]
b = model1.coef_[0][0]
yfit = a + b * X[:, 1]
plt.scatter(X[:, 1], Y, label='Data')
plt.plot(X[:, 1], yfit, color='red', label='Regression Line')
plt.xlabel('horsepower')
plt.ylabel('mpg')
plt.legend()
plt.show()
```

In this code:
- The first two lines import the necessary libraries and read in the data from the CSV file.
- The third line drops rows with missing values.
- The fourth line computes the number of rows in the dataset.
- The fifth line extracts the `horsepower` column as a NumPy array and reshapes it into a 2D array with one column.
- The sixth line extracts the `mpg` column as a NumPy array and reshapes it into a 2D array with one column.
- The seventh line creates a new matrix with ones in the first column and `horsepower` values in the second column.
- The eight line fits a linear regression model to the data using the `LinearRegression` class from Scikit-learn.
- The ninth and tenth lines extract the intercept and coefficient of the fitted model.
- The eleventh line computes the predicted values for `mpg` based on the fitted model.
- The rest of the code uses Matplotlib to create a scatter plot of the data, with the regression line overlaid.
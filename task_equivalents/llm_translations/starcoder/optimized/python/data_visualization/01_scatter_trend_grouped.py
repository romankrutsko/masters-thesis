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

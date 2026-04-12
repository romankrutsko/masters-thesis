import pandas as pd
from sklearn.linear_model import LinearRegression

auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()

X = auto[['horsepower']]
y = auto['mpg']

model1 = LinearRegression()
model1.fit(X, y)
print(f"Intercept: {model1.intercept_:.3f}")
print(f"Coefficients: {model1.coef_[0]:.3f}")

new_data = pd.DataFrame({'horsepower': [98]})
confidence_interval = model1.predict(new_data)
prediction_interval = model1.predict(new_data)

print(f"Confidence interval: {confidence_interval[0]:.3f}")
print(f"Prediction interval: {prediction_interval[0]:.3f}")
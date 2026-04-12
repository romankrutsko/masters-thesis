import pandas as pd
auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()
model1 = sm.OLS(auto['mpg'], sm.add_constant(auto['horsepower'])).fit()
print(model1.summary())
print(model1.get_prediction([1, 98]).summary_frame())

import pandas as pd
import statsmodels.api as sm

# Load data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

# Fit linear model
X = sm.add_constant(auto['horsepower'])
model1 = sm.OLS(auto['mpg'], X).fit()
print(model1.summary())

# Make predictions
new_data = pd.DataFrame({'const': 1, 'horsepower': [98]})
predict_conf = model1.get_prediction(new_data).summary_frame(alpha=0.05)[['mean', 'mean_ci_lower', 'mean_ci_upper']]
predict_pred = model1.get_prediction(new_data).summary_frame(alpha=0.05)[['mean', 'obs_ci_lower', 'obs_ci_upper']]

print(predict_conf)
print(predict_pred)
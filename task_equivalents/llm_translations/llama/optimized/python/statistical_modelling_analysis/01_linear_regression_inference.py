import pandas as pd
import statsmodels.api as sm

# Load data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()

# Fit the model
X = sm.add_constant(auto['horsepower'])
model1 = sm.OLS(auto['mpg'], X).fit()

# Print summary
print(model1.summary())

# Make predictions
new_data = pd.DataFrame({'horsepower': [98]})
new_data = sm.add_constant(new_data)

# Confidence interval
confidence_interval = model1.get_prediction(new_data).summary_frame(alpha=0.05)[['mean', 'mean_ci_lower', 'mean_ci_upper']]
print(confidence_interval)

# Prediction interval
prediction_interval = model1.get_prediction(new_data).summary_frame(alpha=0.05)[['mean', 'obs_ci_lower', 'obs_ci_upper']]
print(prediction_interval)
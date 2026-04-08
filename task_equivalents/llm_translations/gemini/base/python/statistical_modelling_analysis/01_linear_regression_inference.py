import pandas as pd
import statsmodels.formula.api as smf

auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
auto = auto.dropna()

model1 = smf.ols('mpg ~ horsepower', data=auto).fit()
print(model1.summary())

new_data = pd.DataFrame({'horsepower': [98]})
predictions = model1.get_prediction(new_data)
summary_frame = predictions.summary_frame(alpha=0.05)

# Confidence interval
print("Confidence Interval:")
print(summary_frame[['mean', 'mean_ci_lower', 'mean_ci_upper']])

# Prediction interval
print("\nPrediction Interval:")
print(summary_frame[['mean', 'obs_ci_lower', 'obs_ci_upper']])
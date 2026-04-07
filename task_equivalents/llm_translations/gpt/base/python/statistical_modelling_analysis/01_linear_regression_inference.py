import pandas as pd
import statsmodels.formula.api as smf

auto = pd.read_csv("data/csv/Auto.csv", header=0, na_values="?")
auto = auto.dropna()

model1 = smf.ols("mpg ~ horsepower", data=auto).fit()
print(model1.summary())

new_data = pd.DataFrame({"horsepower": [98]})

confidence_pred = model1.get_prediction(new_data).summary_frame(alpha=0.05)
print(confidence_pred[["mean", "mean_ci_lower", "mean_ci_upper"]])

prediction_pred = model1.get_prediction(new_data).summary_frame(alpha=0.05)
print(prediction_pred[["mean", "obs_ci_lower", "obs_ci_upper"]])
import pandas as pd
import statsmodels.formula.api as smf

auto = pd.read_csv("data/csv/Auto.csv", na_values="?").dropna()

model1 = smf.ols("mpg ~ horsepower", data=auto).fit()
print(model1.summary())

new_data = pd.DataFrame({"horsepower": [98]})

conf_pred = model1.get_prediction(new_data).summary_frame(alpha=0.05)
print(conf_pred[["mean", "mean_ci_lower", "mean_ci_upper"]])

pred_pred = model1.get_prediction(new_data).summary_frame(alpha=0.05)
print(pred_pred[["mean", "obs_ci_lower", "obs_ci_upper"]])
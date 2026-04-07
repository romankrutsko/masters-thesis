import pandas as pd

auto = pd.read_csv("data/csv/Auto.csv", na_values="?", index_col=0).dropna()

auto["mpg01"] = (auto["mpg"] > auto["mpg"].median()).astype(int)
auto = auto.drop(columns=["mpg", "name"])

var_no_scale = ["cylinders", "year", "origin", "mpg01"]
var_to_scale = ["displacement", "horsepower", "weight", "acceleration"]

scaled_var = (auto[var_to_scale] - auto[var_to_scale].mean()) / auto[var_to_scale].std(ddof=1)
df = pd.concat([scaled_var, auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df["mpg01"]
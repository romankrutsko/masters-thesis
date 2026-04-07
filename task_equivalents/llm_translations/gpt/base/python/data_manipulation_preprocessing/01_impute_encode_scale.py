import pandas as pd
from sklearn.preprocessing import StandardScaler

Auto = pd.read_csv("data/csv/Auto.csv", header=0, na_values="?", index_col=0)

mpg01 = (Auto["mpg"] > Auto["mpg"].median()).astype(int)
df = Auto.iloc[:, 1:7].copy()
df["mpg01"] = mpg01

# Scale continuous variables; keep binary/categorical-coded columns unscaled.
var_to_scale = ["displacement", "horsepower", "weight", "acceleration"]
scaler = StandardScaler()
df[var_to_scale] = scaler.fit_transform(df[var_to_scale])

x = df.loc[:, df.columns != "mpg01"]
y = df["mpg01"].astype("category")
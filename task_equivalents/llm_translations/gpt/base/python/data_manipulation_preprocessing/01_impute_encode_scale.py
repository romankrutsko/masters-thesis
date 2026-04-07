import pandas as pd
from sklearn.preprocessing import StandardScaler

Auto = pd.read_csv('data/csv/Auto.csv', header=0, na_values='?', index_col=0)
Auto = Auto.dropna()

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(columns=['mpg', 'name'])

# Scale continuous variables; keep binary/categorical-coded columns unscaled.
var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

scaler = StandardScaler()
scaled_var = pd.DataFrame(
    scaler.fit_transform(Auto[var_to_scale]),
    columns=var_to_scale,
    index=Auto.index
)

df = pd.concat([scaled_var, Auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df['mpg01']
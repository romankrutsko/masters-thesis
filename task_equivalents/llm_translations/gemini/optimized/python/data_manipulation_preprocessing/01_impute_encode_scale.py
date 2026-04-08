import pandas as pd

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)
Auto = Auto.dropna()

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(columns=['mpg', 'name'], errors='ignore')

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

scaled_var = (Auto[var_to_scale] - Auto[var_to_scale].mean()) / Auto[var_to_scale].std()
df = pd.concat([scaled_var, Auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df['mpg01']
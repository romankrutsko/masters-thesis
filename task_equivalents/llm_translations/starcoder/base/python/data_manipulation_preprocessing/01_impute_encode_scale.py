import pandas as pd
from sklearn.preprocessing import scale

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?')
Auto.dropna(inplace=True)

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(['mpg', 'name'], axis=1)

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var = scale(Auto[var_to_scale])
df = pd.DataFrame(scaled_var, columns=var_to_scale)

df['cylinders'] = Auto['cylinders']
df['year'] = Auto['year']
df['origin'] = Auto['origin']
df['mpg01'] = Auto['mpg01']

x = df.drop('mpg01', axis=1)
y = df['mpg01']
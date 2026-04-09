import pandas as pd
from sklearn.preprocessing import StandardScaler

# Load data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?').set_index('Unnamed: 0' if 'Unnamed: 0' in pd.read_csv('data/csv/Auto.csv', nrows=0).columns else None)
auto = auto.dropna()

# Create a new column 'mpg01'
auto['mpg01'] = (auto['mpg'] > auto['mpg'].median()).astype(int)

# Drop unnecessary columns
auto = auto.drop(['mpg', 'name'], axis=1)

# Scale continuous variables; keep binary/categorical-coded columns unscaled.
var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

scaler = StandardScaler()
scaled_var = scaler.fit_transform(auto[var_to_scale])
scaled_df = pd.DataFrame(scaled_var, columns=var_to_scale, index=auto.index)

df = pd.concat([scaled_df, auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df['mpg01']
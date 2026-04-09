import pandas as pd
from sklearn.preprocessing import scale

# Load data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)

# Drop rows with missing values
auto = auto.dropna()

# Create a binary column 'mpg01'
auto['mpg01'] = (auto['mpg'] > auto['mpg'].median()).astype(int)

# Drop 'mpg' and 'name' columns
auto = auto.drop(columns=['mpg', 'name'])

# Define columns to scale and not to scale
var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

# Scale continuous variables
auto[var_to_scale] = scale(auto[var_to_scale])

# Split data into features and target
x = auto.drop(columns='mpg01')
y = auto['mpg01']
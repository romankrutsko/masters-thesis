import pandas as pd
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Load data
Auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna().set_index('name')

# Create new column
Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)

# Select relevant columns
var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
Auto = Auto[var_to_scale + var_no_scale]

# Scale relevant columns
scaler = ColumnTransformer([('scaler', StandardScaler(), var_to_scale)], remainder='passthrough')
x = Auto.drop('mpg01', axis=1)
y = Auto['mpg01']

# Define tuning parameters
ctry = [0.01, 0.1, 1, 10, 100, 1000]
param_grid_linear = {'svm__C': ctry}
param_grid_poly = {'svm__C': ctry, 'svm__degree': [2, 3, 4, 5]}
param_grid_radial = {'svm__C': ctry, 'svm__gamma': [0.5, 1, 2, 3]}

# Define pipeline and tune
pipeline = Pipeline([('scaler', scaler), ('svm', svm.SVC())])

# Linear kernel
grid_search_linear = GridSearchCV(pipeline, param_grid_linear, cv=5)
grid_search_linear.fit(x, y)
print("Linear Kernel:")
print(grid_search_linear.best_params_)
print(grid_search_linear.best_score_)

# Polynomial kernel
param_grid_poly = {'svm__C': ctry, 'svm__degree': [2, 3, 4, 5], 'svm__kernel': ['poly']}
pipeline_poly = Pipeline([('scaler', scaler), ('svm', svm.SVC(kernel='poly'))])
grid_search_poly = GridSearchCV(pipeline_poly, {'svm__C': ctry, 'svm__degree': [2, 3, 4, 5]}, cv=5)
grid_search_poly.fit(x, y)
print("\nPolynomial Kernel:")
print(grid_search_poly.best_params_)
print(grid_search_poly.best_score_)

# Radial kernel
pipeline_radial = Pipeline([('scaler', scaler), ('svm', svm.SVC(kernel='rbf'))])
grid_search_radial = GridSearchCV(pipeline_radial, param_grid_radial, cv=5)
grid_search_radial.fit(x, y)
print("\nRadial Kernel:")
print(grid_search_radial.best_params_)
print(grid_search_radial.best_score_)
import pandas as pd
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Load data
auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0).dropna()

# Preprocess data
auto['mpg01'] = (auto['mpg'] > auto['mpg'].median()).astype(int)
auto = auto.drop(['mpg', 'name'], axis=1)

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

# Split data into features and target
x = auto[var_to_scale + var_no_scale[:-1]]
y = auto['mpg01'].astype('category').cat.codes

# Define pipelines and hyperparameter tuning spaces
ctry = [0.01, 0.1, 1, 10, 100, 1000]
tune_ctrl = {'cv': 5}

pipelines = {
    'linear': Pipeline([('scaler', StandardScaler()), ('svm', svm.SVC(kernel='linear'))]),
    'polynomial': Pipeline([('scaler', StandardScaler()), ('svm', svm.SVC(kernel='poly'))]),
    'radial': Pipeline([('scaler', StandardScaler()), ('svm', svm.SVC(kernel='rbf'))])
}

param_grids = {
    'linear': {'svm__C': ctry},
    'polynomial': {'svm__C': ctry, 'svm__degree': [2, 3, 4, 5]},
    'radial': {'svm__C': ctry, 'svm__gamma': [0.5, 1, 2, 3]}
}

# Perform hyperparameter tuning
for kernel, pipeline in pipelines.items():
    grid_search = GridSearchCV(pipeline, param_grids[kernel], **tune_ctrl, random_state=1)
    grid_search.fit(x, y)
    print(f"Kernel: {kernel}")
    print(grid_search.cv_results_)
    print(f"Best Parameters: {grid_search.best_params_}")
    print(f"Best Score: {grid_search.best_score_}")
    print()
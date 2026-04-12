import pandas as pd
from sklearn.preprocessing import scale
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

df = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)
df = df.dropna()

df['mpg01'] = (df['mpg'] > df['mpg'].median()).astype(int)
df = df.drop(['mpg', 'name'], axis=1)

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var = scale(df[var_to_scale])
df = pd.concat([pd.DataFrame(scaled_var, columns=var_to_scale), df[var_no_scale]], axis=1)

x = df.drop('mpg01', axis=1)
y = df['mpg01']
ctry = [0.01, 0.1, 1, 10, 100, 1000]

param_grid = {'C': ctry}
svm_linear = SVC(kernel='linear')
grid_search = GridSearchCV(svm_linear, param_grid, cv=5)
grid_search.fit(x, y)
print(grid_search.best_params_)
print(grid_search.best_score_)

polytry = [2, 3, 4, 5]
param_grid = {'C': ctry, 'degree': polytry}
svm_poly = SVC(kernel='poly')
grid_search = GridSearchCV(svm_poly, param_grid, cv=5)
grid_search.fit(x, y)
print(grid_search.best_params_)
print(grid_search.best_score_)

gammatry = [0.5, 1, 2, 3]
param_grid = {'C': ctry, 'gamma': gammatry}
svm_rbf = SVC(kernel='rbf')
grid_search = GridSearchCV(svm_rbf, param_grid, cv=5)
grid_search.fit(x, y)
print(grid_search.best_params_)
print(grid_search.best_score_)
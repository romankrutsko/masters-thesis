import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, KFold

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)
Auto = Auto.dropna()

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(columns=['mpg', 'name'], errors='ignore')

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']

scaled_var = (Auto[var_to_scale] - Auto[var_to_scale].mean()) / Auto[var_to_scale].std(ddof=1)
df = pd.concat([scaled_var, Auto[var_no_scale]], axis=1)

X = df.drop(columns=['mpg01'])
y = df['mpg01']

ctry = [0.01, 0.1, 1, 10, 100, 1000]
cv_ctrl = KFold(n_splits=5, shuffle=True, random_state=1)

# Linear Kernel
tune_out1 = GridSearchCV(SVC(kernel='linear'), param_grid={'C': ctry}, cv=cv_ctrl)
tune_out1.fit(X, y)
print("Linear Kernel Tuning Summary:")
print(pd.DataFrame(tune_out1.cv_results_)[['params', 'mean_test_score', 'std_test_score']])

# Polynomial Kernel
polytry = [2, 3, 4, 5]
tune_out2 = GridSearchCV(SVC(kernel='poly'), param_grid={'C': ctry, 'degree': polytry}, cv=cv_ctrl)
tune_out2.fit(X, y)
print("\nPolynomial Kernel Tuning Summary:")
print(pd.DataFrame(tune_out2.cv_results_)[['params', 'mean_test_score', 'std_test_score']])

# Radial Kernel
gammatry = [0.5, 1, 2, 3]
tune_out3 = GridSearchCV(SVC(kernel='rbf'), param_grid={'C': ctry, 'gamma': gammatry}, cv=cv_ctrl)
tune_out3.fit(X, y)
print("\nRadial Kernel Tuning Summary:")
print(pd.DataFrame(tune_out3.cv_results_)[['params', 'mean_test_score', 'std_test_score']])
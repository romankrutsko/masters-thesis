import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, KFold

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?', index_col=0)
Auto = Auto.dropna()

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(columns=['mpg', 'name'])

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var = (Auto[var_to_scale] - Auto[var_to_scale].mean()) / Auto[var_to_scale].std(ddof=1)
df = pd.concat([scaled_var, Auto[var_no_scale]], axis=1)

x = df.iloc[:, :-1]
y = df['mpg01']

ctry = [0.01, 0.1, 1, 10, 100, 1000]
kf = KFold(n_splits=5, shuffle=True, random_state=1)

# Linear kernel
tune_out1 = GridSearchCV(SVC(kernel='linear'), param_grid={'C': ctry}, cv=kf)
tune_out1.fit(x, y)
# Equivalent to summary(tune.out1)
for k in ['mean_test_score', 'std_test_score', 'params']:
    print(f"{k}: {tune_out1.cv_results_[k]}")
print(f"Best params: {tune_out1.best_params_}\n")

# Polynomial kernel
polytry = [2, 3, 4, 5]
tune_out2 = GridSearchCV(SVC(kernel='poly'), param_grid={'C': ctry, 'degree': polytry}, cv=kf)
tune_out2.fit(x, y)
for k in ['mean_test_score', 'std_test_score', 'params']:
    print(f"{k}: {tune_out2.cv_results_[k]}")
print(f"Best params: {tune_out2.best_params_}\n")

# Radial kernel
gammatry = [0.5, 1, 2, 3]
tune_out3 = GridSearchCV(SVC(kernel='rbf'), param_grid={'C': ctry, 'gamma': gammatry}, cv=kf)
tune_out3.fit(x, y)
for k in ['mean_test_score', 'std_test_score', 'params']:
    print(f"{k}: {tune_out3.cv_results_[k]}")
print(f"Best params: {tune_out3.best_params_}")
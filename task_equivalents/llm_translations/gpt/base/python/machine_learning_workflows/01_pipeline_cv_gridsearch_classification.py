import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, StratifiedKFold

Auto = pd.read_csv('data/csv/Auto.csv', header=0, na_values='?', index_col=0)
Auto = Auto.dropna()

Auto['mpg01'] = (Auto['mpg'] > Auto['mpg'].median()).astype(int)
Auto = Auto.drop(columns=['mpg', 'name'])

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
y = df['mpg01'].astype('category')

ctry = [0.01, 0.1, 1, 10, 100, 1000]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)

tune_out1 = GridSearchCV(
    SVC(kernel='linear'),
    param_grid={'C': ctry},
    cv=cv
)
tune_out1.fit(x, y)
print('Linear kernel best params:', tune_out1.best_params_)
print('Linear kernel best score:', tune_out1.best_score_)
print(pd.DataFrame(tune_out1.cv_results_)[['params', 'mean_test_score', 'std_test_score']])

polytry = [2, 3, 4, 5]

tune_out2 = GridSearchCV(
    SVC(kernel='poly'),
    param_grid={'C': ctry, 'degree': polytry},
    cv=cv
)
tune_out2.fit(x, y)
print('Polynomial kernel best params:', tune_out2.best_params_)
print('Polynomial kernel best score:', tune_out2.best_score_)
print(pd.DataFrame(tune_out2.cv_results_)[['params', 'mean_test_score', 'std_test_score']])

gammatry = [0.5, 1, 2, 3]

tune_out3 = GridSearchCV(
    SVC(kernel='rbf'),
    param_grid={'C': ctry, 'gamma': gammatry},
    cv=cv
)
tune_out3.fit(x, y)
print('Radial kernel best params:', tune_out3.best_params_)
print('Radial kernel best score:', tune_out3.best_score_)
print(pd.DataFrame(tune_out3.cv_results_)[['params', 'mean_test_score', 'std_test_score']])
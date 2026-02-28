# Extracted from Ch09.py (Q7 SVM workflow + GridSearchCV)

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

Auto = pd.read_csv('C:\\Users\\Carol\\Desktop\\Auto.csv', na_values='?').dropna()
Auto['mpg01'] = np.where(Auto['mpg'] > np.median(Auto['mpg']), 1, 0)
Auto          = Auto.drop(['mpg', 'name'], axis=1)
var_no_scale  = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale  = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var    = StandardScaler().fit_transform(Auto[var_to_scale])
temp1         = pd.DataFrame(scaled_var, columns=var_to_scale)
temp2         = Auto[var_no_scale].reset_index(drop=True)
df            = pd.concat([temp1, temp2], axis=1)
x             = df.iloc[:,:-1]
y             = df['mpg01']

tune_param = [{'C': [0.01, 0.1, 1, 10]}]
tune_out   = GridSearchCV(SVC(kernel='linear'), tune_param, cv=5, scoring='accuracy', n_jobs=-1)
tune_out.fit(x, y)
best_svc   = tune_out.best_estimator_
print('best cost for SVC %s' %tune_out.best_params_)

tune_param = [{'C': [0.01, 0.1, 1, 10], 'degree': [2, 3, 4]}]
tune_out   = GridSearchCV(SVC(kernel='poly'), tune_param, cv=5, scoring='accuracy', n_jobs=-1)
tune_out.fit(x, y)
best_svmp  = tune_out.best_estimator_
print('best cost for SVM poly %s' %tune_out.best_params_)

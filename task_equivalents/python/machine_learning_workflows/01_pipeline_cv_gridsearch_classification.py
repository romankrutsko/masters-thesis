# Extracted from Ch09.py (Q7 SVM + GridSearchCV workflow)

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

Auto = pd.read_csv('data/csv/Auto.csv', na_values='?').dropna()
Auto['mpg01'] = np.where(Auto['mpg'] > np.median(Auto['mpg']), 1, 0)
Auto = Auto.drop(['mpg', 'name'], axis=1)

var_no_scale = ['cylinders', 'year', 'origin', 'mpg01']
var_to_scale = ['displacement', 'horsepower', 'weight', 'acceleration']
scaled_var = StandardScaler().fit_transform(Auto[var_to_scale])
df = pd.concat([
    pd.DataFrame(scaled_var, columns=var_to_scale),
    Auto[var_no_scale].reset_index(drop=True)
], axis=1)

x = df.iloc[:, :-1]
y = df['mpg01']

tune_param = [{'C': [0.01, 0.1, 1, 10, 100, 1000]}]
GridSearchCV(SVC(kernel='linear'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)

tune_param = [{'C': [0.01, 0.1, 1, 10, 100, 1000], 'degree': [2, 3, 4, 5]}]
GridSearchCV(SVC(kernel='poly'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)

tune_param = [{'C': [0.01, 0.1, 1, 10, 100, 1000], 'gamma': [0.5, 1, 2, 3]}]
GridSearchCV(SVC(kernel='rbf'), tune_param, cv=5, scoring='accuracy', n_jobs=-1).fit(x, y)

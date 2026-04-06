# Extracted from Ch06.py (Q9 preprocessing/model setup)

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

College = pd.read_csv('data/csv/College.csv')
school_name = College.iloc[:, 0]
College = College.rename(index=lambda i: school_name[i])
College.drop(College.columns[[0]], axis=1, inplace=True)

College['Private01'] = np.where(College.Private == 'Yes', 1, 0)
College.drop(['Private'], axis=1, inplace=True)

X = College.drop(['Apps'], axis=1).astype('float64')
Y = College['Apps']
xtrain, xtest, ytrain, ytest = train_test_split(X, Y, test_size=0.5, random_state=1)
